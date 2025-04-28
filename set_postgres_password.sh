#!/bin/bash
# Script to set PostgreSQL password

# Default values
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="adv62062"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --user)
      POSTGRES_USER="$2"
      shift 2
      ;;
    --password)
      POSTGRES_PASSWORD="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Update database.json
if [ -f "config/database.json" ]; then
    echo "Updating PostgreSQL password in config/database.json"
    # Use sed to update the password
    sed -i "s/\"password\": \"[^\"]*\"/\"password\": \"$POSTGRES_PASSWORD\"/" config/database.json
    sed -i "s/\"user\": \"[^\"]*\"/\"user\": \"$POSTGRES_USER\"/" config/database.json
    echo "Updated config/database.json"
else
    echo "config/database.json not found"
fi

# Update .env file
if [ -f ".env" ]; then
    echo "Updating PostgreSQL password in .env"
    # Use sed to update the password
    sed -i "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$POSTGRES_PASSWORD/" .env
    sed -i "s/POSTGRES_USER=.*/POSTGRES_USER=$POSTGRES_USER/" .env
    echo "Updated .env"
else
    echo ".env not found"
fi

echo "PostgreSQL credentials updated:"
echo "User: $POSTGRES_USER"
echo "Password: $POSTGRES_PASSWORD"
echo ""
echo "You may need to restart the system for changes to take effect."
