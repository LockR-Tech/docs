# export.sh <glob-prefix>: render out/drawio/<prefix>*.drawio -> out/png
cd "$(dirname "$0")/../out"; mkdir -p png
for f in drawio/$1*.drawio; do b=$(basename "$f" .drawio)
  if [ ! -f "png/$b.png" ] || [ "$f" -nt "png/$b.png" ]; then "/c/Program Files/draw.io/draw.io.exe" -x -f png -s 2 -b 14 -o "png/$b.png" "$f" >/dev/null 2>&1; fi
done
