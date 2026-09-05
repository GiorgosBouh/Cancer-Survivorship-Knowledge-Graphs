#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 3 ]; then
  echo "Usage: $0 URL OUTPUT_PATH SIZE_BYTES [PARTS] [MAX_JOBS]" >&2
  exit 2
fi

url="$1"
out="$2"
size="$3"
parts="${4:-16}"
max_jobs="${5:-8}"
segdir="${out}.segments"
mkdir -p "$segdir" "$(dirname "$out")"

actual_size() {
  if [ -f "$1" ]; then
    stat -c '%s' "$1"
  else
    echo 0
  fi
}

if [ -f "$out" ] && [ "$(actual_size "$out")" -eq "$size" ]; then
  echo "Already complete: $out"
  exit 0
fi

chunk=$(( (size + parts - 1) / parts ))
active=0
for i in $(seq 0 $((parts - 1))); do
  start=$(( i * chunk ))
  if [ "$start" -ge "$size" ]; then
    break
  fi
  end=$(( start + chunk - 1 ))
  if [ "$end" -ge "$size" ]; then
    end=$(( size - 1 ))
  fi
  expected=$(( end - start + 1 ))
  seg=$(printf '%s/part_%03d' "$segdir" "$i")
  if [ -f "$seg" ] && [ "$(actual_size "$seg")" -eq "$expected" ]; then
    echo "Segment $i already complete"
    continue
  fi

  (
    echo "Downloading segment $i bytes $start-$end"
    curl -sS -fL --retry 8 --retry-delay 5 --range "$start-$end" -o "${seg}.tmp" "$url"
    got=$(actual_size "${seg}.tmp")
    if [ "$got" -ne "$expected" ]; then
      echo "Segment $i size mismatch: got $got expected $expected" >&2
      exit 1
    fi
    mv "${seg}.tmp" "$seg"
  ) &
  active=$((active + 1))
  if [ "$active" -ge "$max_jobs" ]; then
    wait -n
    active=$((active - 1))
  fi
done
wait

for i in $(seq 0 $((parts - 1))); do
  start=$(( i * chunk ))
  if [ "$start" -ge "$size" ]; then
    break
  fi
  end=$(( start + chunk - 1 ))
  if [ "$end" -ge "$size" ]; then
    end=$(( size - 1 ))
  fi
  expected=$(( end - start + 1 ))
  seg=$(printf '%s/part_%03d' "$segdir" "$i")
  got=$(actual_size "$seg")
  if [ "$got" -ne "$expected" ]; then
    echo "Segment $i incomplete: got $got expected $expected" >&2
    exit 1
  fi
done

cat "$segdir"/part_* > "${out}.assembled"
got=$(actual_size "${out}.assembled")
if [ "$got" -ne "$size" ]; then
  echo "Assembled size mismatch: got $got expected $size" >&2
  exit 1
fi
mv "${out}.assembled" "$out"
echo "Complete: $out"
