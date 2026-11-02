#!/bin/bash
# Crée une base et un rôle par service. Exécuté par l'image postgres à la première
# initialisation du volume uniquement. Les mots de passe viennent de l'environnement.
set -e

for service in users meals bookings accounts; do
  variable="$(echo "$service" | tr '[:lower:]' '[:upper:]')_DB_PASSWORD"
  password="${!variable}"
  psql -v ON_ERROR_STOP=1 -v password="$password" --username "$POSTGRES_USER" --dbname postgres <<SQL
CREATE ROLE ${service} LOGIN PASSWORD :'password';
CREATE DATABASE ${service} OWNER ${service};
REVOKE CONNECT ON DATABASE ${service} FROM PUBLIC;
SQL
done
