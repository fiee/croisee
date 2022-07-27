#!/bin/bash
echo "Copy database backup and media from server"
USER=croisee
SERVER=${USER}.fiee.net
ISODATE=`date +"%Y-%m-%d"`
#YESTERDATE=`date -v-1d +"%Y-%m-%d"`

# Backup is saved every day at 02:02, thus today’s backup should be available
echo "Fetching database backup"
rsync ${USER}@${SERVER}:/var/www/${USER}/backup/${USER}_${ISODATE}.sql.gz ./media/

#echo "Copying media"
#rsync -az ${USER}@${SERVER}:/var/www/${USER}/${USER}/media/ ./media

echo "Installing database"
source .env
gunzip < media/${USER}_${ISODATE}.sql.gz | mysql -u${USER} -p${DATABASE_PASSWORD} -D${USER}
