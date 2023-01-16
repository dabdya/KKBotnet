if [ "$1" == "-h" ]; then
  echo "Usage: `basename $0` [network-folder] [instance-name]"
  exit 0
fi

# Import variables from config.cfg file
source <(cat config.env | sed -e '/^#/d;/^\s*$/d' -e "s/'/'\\\''/g" -e "s/=\(.*\)/='\1'/g")

# Default folder is `default`. Check `yc resource-manager folder list`
NETWORK_FOLDER=${1:-"default"}

# Generate instance name if not specified
INSTANCE_NAME=${2:-$(cat /dev/urandom | tr -dc 'a-z' | fold -w 10 | head -n 1)}

# Random zone choice
ZONE_CHOICES[0]="ru-central1-a"
ZONE_CHOICES[1]="ru-central1-b"
ZONE_CHOICES[2]="ru-central1-c"

RANDOM_INDEX=$[ $RANDOM % 3 ]
ZONE=${ZONE_CHOICES[$RANDOM_INDEX]}

# Create subnet name
SUBNET_NAME=$NETWORK_FOLDER-$ZONE

# Assembly point for create instance with docker-compose
yc compute instance create \
  --cloud-id $CLOUD_ID \
  --name $INSTANCE_NAME \
  --zone $ZONE \
  --create-boot-disk image-folder-id=standard-images,image-family=ubuntu-2004-lts \
  --network-interface subnet-name=$SUBNET_NAME,nat-ip-version=ipv4 \
  --ssh-key keys/id_rsa.pub \
  --async
