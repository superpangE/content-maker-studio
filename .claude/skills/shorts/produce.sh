#!/usr/bin/env bash
#
# produce.sh — Layer 2 render script for a short.
#
# Reads shots.json in this folder and renders a 9:16 MP4:
#   1. TTS  : narration line per shot  -> shot_<id>.mp3   (ElevenLabs)
#   2. Video: veo_prompt per shot      -> shot_<id>.mp4   (Veo)
#   3. Burn caption + mux narration per shot, then concat -> out_<platform>.mp4
#
# Layer design: NO API keys are required to *have* this script. It checks for
# keys + tools at run time. If anything is missing it prints exactly what's
# needed and exits 0 (it does not crash the pipeline).
#
# Required env vars to actually render:
#   ELEVENLABS_API_KEY   - TTS
#   VEO_API_KEY          - text-to-video
# Required tools: ffmpeg, ffprobe, python3, curl
#
# IMPORTANT: The two API call functions (tts_elevenlabs, video_veo) use the
# best-known request shapes at authoring time. Provider APIs change — confirm
# the current endpoint/params in your provider's docs before relying on it.
# Everything else (parsing, assembly, caption burn-in) is provider-independent.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHOTS_JSON="$HERE/shots.json"
WORK="$HERE/render"          # intermediate artifacts (created after preflight passes)

# ---- preflight ---------------------------------------------------------------

missing=0
need() { command -v "$1" >/dev/null 2>&1 || { echo "  ✗ 도구 없음: $1"; missing=1; }; }
needvar() { [ -n "${!1:-}" ] || { echo "  ✗ 환경변수 없음: $1"; missing=1; }; }

echo "== produce.sh 사전 점검 =="
[ -f "$SHOTS_JSON" ] || { echo "  ✗ shots.json 이 폴더에 없습니다: $SHOTS_JSON"; exit 1; }
need ffmpeg
need ffprobe
need python3
need curl
needvar ELEVENLABS_API_KEY
needvar VEO_API_KEY

if [ "$missing" -ne 0 ]; then
  cat <<'EOF'

영상을 렌더하려면 위 항목이 필요합니다.

  # 도구 설치 (macOS)
  brew install ffmpeg python3 curl

  # API 키 설정
  export ELEVENLABS_API_KEY=...   # https://elevenlabs.io  (TTS)
  export VEO_API_KEY=...          # 영상 생성 API (Veo 등)

그다음 이 폴더에서 다시 실행하세요:
  ./produce.sh

지금은 스펙(shots.json / storyboard.md)만 준비된 상태이며, 키 없이도
대본·장면 명세는 모두 사용할 수 있습니다.
EOF
  exit 0
fi

mkdir -p "$WORK"   # preflight passed — now stage intermediate artifacts

# ---- read shots.json ---------------------------------------------------------

# Emit shot fields as tab-separated lines: id  duration  narration  veo_prompt  caption
read_shots() {
  python3 - "$SHOTS_JSON" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
for s in d["shots"]:
    fields = [str(s["id"]), str(s["duration_sec"]),
              s["narration"], s["veo_prompt"], s["caption"]]
    print("\t".join(f.replace("\t", " ").replace("\n", " ") for f in fields))
PY
}

# get_json <dotted.path>  e.g.  get_json voice.voice_id
get_json() {
  python3 - "$SHOTS_JSON" "$1" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
for k in sys.argv[2].split("."):
    d = d[k]
print(d)
PY
}

VOICE_ID="$(get_json voice.voice_id)"
RES="$(get_json resolution)"     # e.g. 1080x1920
FPS="$(get_json fps)"
W="${RES%x*}"; H="${RES#*x}"

if [ "$VOICE_ID" = "REPLACE_ME" ]; then
  echo "  ✗ shots.json 의 voice.voice_id 가 REPLACE_ME 입니다. 실제 ElevenLabs voice_id 로 바꾸세요."
  exit 0
fi

# ---- provider calls (confirm request shapes against current provider docs) ---

# tts_elevenlabs <text> <out.mp3>
tts_elevenlabs() {
  local text="$1" out="$2"
  curl -sS -X POST \
    "https://api.elevenlabs.io/v1/text-to-speech/${VOICE_ID}" \
    -H "xi-api-key: ${ELEVENLABS_API_KEY}" \
    -H "Content-Type: application/json" \
    -d "$(python3 -c 'import json,sys; print(json.dumps({"text":sys.argv[1],"model_id":"eleven_multilingual_v2"}))' "$text")" \
    --output "$out"
}

# video_veo <prompt> <duration_sec> <out.mp4>
# NOTE: Veo's HTTP surface varies by access (Vertex AI vs. Gemini API) and is
# often async (submit -> poll -> download). Implement the submit/poll for YOUR
# access tier here. The placeholder below documents the contract and fails loud.
video_veo() {
  local prompt="$1" dur="$2" out="$3"
  echo "  ! video_veo: Veo 호출 로직을 사용자의 접근 방식(Vertex AI / Gemini API)에 맞게 구현하세요." >&2
  echo "    prompt=[$prompt] dur=${dur}s -> $out" >&2
  return 1
}

# ---- per-shot render ---------------------------------------------------------

shot_ids=()
while IFS=$'\t' read -r id dur narration veo_prompt caption; do
  [ -z "${id:-}" ] && continue
  shot_ids+=("$id")
  mp3="$WORK/shot_${id}.mp3"
  raw_mp4="$WORK/shot_${id}_raw.mp4"
  fin_mp4="$WORK/shot_${id}.mp4"

  echo "== Shot $id (${dur}s) =="

  # 1) TTS
  echo "  - TTS 생성..."
  tts_elevenlabs "$narration" "$mp3"

  # 2) Video
  echo "  - 영상 생성..."
  video_veo "$veo_prompt" "$dur" "$raw_mp4"

  # 3) Normalize to 9:16, burn caption, mux narration, fix to exact duration.
  #    Caption is escaped for ffmpeg drawtext.
  esc_caption="$(printf '%s' "$caption" | sed "s/'/\\\\'/g; s/:/\\\\:/g")"
  echo "  - 자막 합성 + 길이 정규화..."
  ffmpeg -y -i "$raw_mp4" -i "$mp3" \
    -vf "scale=${W}:${H}:force_original_aspect_ratio=increase,crop=${W}:${H},\
drawtext=text='${esc_caption}':fontcolor=white:fontsize=64:box=1:boxcolor=black@0.55:\
boxborderw=20:x=(w-text_w)/2:y=h-460:line_spacing=10" \
    -r "$FPS" -t "$dur" \
    -map 0:v -map 1:a -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest \
    "$fin_mp4"
done < <(read_shots)

# ---- concat shots ------------------------------------------------------------

concat_list="$WORK/concat.txt"
: > "$concat_list"
for id in "${shot_ids[@]}"; do
  echo "file 'shot_${id}.mp4'" >> "$concat_list"
done

OUT="$HERE/out.mp4"
echo "== 최종 합치기 -> $OUT =="
ffmpeg -y -f concat -safe 0 -i "$concat_list" -c copy "$OUT"

echo "✅ 렌더 완료: $OUT"
echo "   플랫폼별 CTA 변형은 shots.json 의 cta_variants 를 참고해 마지막 컷을 교체하세요."
