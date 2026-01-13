VERSION=$1
RELEASE_NAME=$2

echo "Finding release ID..."

release_id=$(curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$REPO/releases | \
  jq --arg ver "$VERSION" '.[] | select(.name == $ver) | .id')

if [ -z "$release_id" ]; then
  echo "Release not found!"
  exit 1
fi
echo "Release ID: $release_id"

echo "Finding AntaresWeb asset ID..."
asset_id=$(curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$REPO/releases/$release_id/assets | \
  jq --arg release "$RELEASE_NAME" \
   '.[] | select(.name == ($release + ".zip")) | .id')

if [ -z "$asset_id" ]; then
  echo "Asset not found!"
  exit 1
fi
echo "Asset ID: $asset_id"

echo "Downloading asset..."
curl -L -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/octet-stream" \
  https://api.github.com/repos/$REPO/releases/assets/$asset_id \
  -o "$RELEASE_NAME".zip