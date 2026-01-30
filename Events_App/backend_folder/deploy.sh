#!/bin/bash
set -e

echo "🔨 Building frontend..."
cd "$(dirname "$0")"
npm run build:frontend

echo "✅ Build complete. Verifying assets..."
if [ ! -f "dist/index.html" ]; then
  echo "❌ Error: dist/index.html not found!"
  exit 1
fi

# Extract asset names from index.html
JS_ASSET=$(grep -o 'src="/assets/[^"]*' dist/index.html | sed 's|src="/assets/||' | head -1)
CSS_ASSET=$(grep -o 'href="/assets/[^"]*' dist/index.html | sed 's|href="/assets/||' | head -1)

if [ -z "$JS_ASSET" ] || [ -z "$CSS_ASSET" ]; then
  echo "❌ Error: Could not extract asset names from index.html"
  exit 1
fi

if [ ! -f "dist/assets/$JS_ASSET" ]; then
  echo "❌ Error: JS asset not found: dist/assets/$JS_ASSET"
  echo "Available assets:"
  ls -la dist/assets/ || echo "dist/assets/ directory not found!"
  exit 1
fi

if [ ! -f "dist/assets/$CSS_ASSET" ]; then
  echo "❌ Error: CSS asset not found: dist/assets/$CSS_ASSET"
  echo "Available assets:"
  ls -la dist/assets/ || echo "dist/assets/ directory not found!"
  exit 1
fi

echo "✅ Assets verified:"
echo "   JS:  $JS_ASSET"
echo "   CSS: $CSS_ASSET"
echo ""
echo "📦 Checking what will be deployed..."
echo "   dist folder size: $(du -sh dist | cut -f1)"
echo "   dist/index.html references: $JS_ASSET and $CSS_ASSET"
echo ""
read -p "🚀 Deploy to App Engine? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Deployment cancelled."
  exit 0
fi

gcloud app deploy app.yaml

