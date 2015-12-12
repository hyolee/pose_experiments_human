import boto
conn = boto.connect_s3()

bucket_name = 'rosch_pose_simple5'
bucket = conn.get_bucket(bucket_name)
for key in bucket.list():
    key.delete()
conn.delete_bucket(bucket_name)
