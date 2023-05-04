echo $MY_NODE_NAME
echo $ZONE
echo $IMAGE_NAME
attached=$(gcloud compute instances describe $MY_NODE_NAME --zone=$ZONE |  grep sd-lib-disk-)
if [ "$attached" != "" ];
then
    echo "gke node $MY_NODE_NAME already attached a disk."
    exit 0
fi;

flag=0

export PROJECT_ID=$(gcloud config get-value project)
export disks=$(gcloud compute disks list --zones=$ZONE  --format="value(name)" --filter="name ~ ^sd-lib-disk")
echo $PROJECT_ID
echo $disks
disks_arr=($disks)
echo $disks_arr
disks_arr=($(shuf -e "${disks_arr[@]}"))

for i in "${disks_arr[@]}"
do
   echo $i
   disk=$(gcloud compute disks describe $i --zone=$ZONE --format="value(users)")
   echo $disk
   if [ "$disk" = "" ];
   then
       echo "Disk $disk is Free"
       gcloud compute instances attach-disk ${MY_NODE_NAME} --disk=projects/$PROJECT_ID/zones/$ZONE/disks/$i --zone=$ZONE
       return=$?
       echo $return
       if [ "$return" -eq 0 ];
       then
         flag=1
         break
       else
         echo "disk is free, but booked by another node"
         sleep 5
         continue
       fi;
   else
       echo "Disk $disk is Busy"
   fi;
done

if [ $flag = 0 ];
then
  NOW=$(date +"%Y%m%H%M%S")
  #gcloud compute disks create sd-lib-disk-$NOW --type=pd-balanced --size=30GB --zone=$ZONE --source-snapshot=projects/$PROJECT_ID/global/snapshots/$SNAPSHOT_NAME
  gcloud compute disks create sd-lib-disk-$NOW --type=pd-balanced --size=30GB --zone=$ZONE --image=$IMAGE_NAME
  gcloud compute instances attach-disk ${MY_NODE_NAME} --disk=projects/$PROJECT_ID/zones/$ZONE/disks/sd-lib-disk-$NOW --zone=$ZONE
fi;
