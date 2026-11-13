#!/usr/bin/env bash
# deploy/azure/deploy.sh — Langkah 15 (PDF Hal. 30):
# Skrip 1-perintah deploy ke Azure Container Apps (Azure for Students $100 kredit gratis)
set -euo pipefail

RESOURCE_GROUP="${RESOURCE_GROUP:-rg-signbridge-asean}"
LOCATION="${LOCATION:-southeastasia}"
ENVIRONMENT="${ENVIRONMENT:-env-signbridge}"
APP_NAME="${APP_NAME:-signbridge-asean}"

echo "[1/3] Membuat Resource Group $RESOURCE_GROUP di $LOCATION..."
az group create --name "$RESOURCE_GROUP" --location "$LOCATION"

echo "[2/3] Membangun & men-deploy Container App $APP_NAME..."
az containerapp up \
  --name "$APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --environment "$ENVIRONMENT" \
  --source . \
  --ingress external \
  --target-port 7860

echo "[3/3] Selesai! Aplikasi SignBridge ASEAN aktif di HTTPS publik."

