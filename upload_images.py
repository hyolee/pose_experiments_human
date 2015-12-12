import boto
import cPickle
import numpy as np
import yamutils.fast as fast

cat = 'bear'
bucket_name = 'rosch_pose'
query_inds = np.arange(100)

def publish_images(cat, query_inds, bucket_name, dummy_upload=True):
    im_pth = '/home/hyo/.skdata/genthor/RoschDataset3_' + cat + '_6eef6648406c333a4035cd5e60d0bf2ecf2606d7/cache/568ce4d00d2c7901515e71c0f90628db084f9dc6/jpeg/'
    meta_pth = '/home/hyo/.skdata/genthor/RoschDataset3_' + cat + '_6eef6648406c333a4035cd5e60d0bf2ecf2606d7/meta.pkl'
    meta = cPickle.load(open(meta_pth))

    if 'filename' not in meta.dtype.names:    
        # save filenames
        perm = np.random.RandomState(0).permutation(len(meta)) 
        pinv = fast.perminverse(perm)
        filename = [im_pth + str(pinv[i]) + '.jpeg' for i in range(len(meta))]
        meta = meta.addcols(filename, names='filename')
        with open(meta_pth, 'w') as f:
            cPickle.dump(meta, f)
    
    # publish to s3
    conn = boto.connect_s3()
    b = conn.create_bucket(bucket_name)
    urls = [ ]
    for count, ind in enumerate(query_inds):
        name = cat + '_' + str(meta['id'][ind]) + '.jpeg'
        url = 'https://s3.amazonaws.com/' + bucket_name + '/' + name
        urls.append(url)
        if not dummy_upload:
            if count % 100 == 0:
                print str(count) + ' of ' + str(len(query_inds))
            k = b.new_key(name)
            k.set_contents_from_filename(meta['filename'][ind], policy='public-read')
    return urls
