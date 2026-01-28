# -*- coding: utf-8 -*-

import oss2

class OSS:
    def upload(self, filename, filepath):
        endpoint = 'http://oss-rg-china-mainland.aliyuncs.com' # Suppose that your bucket is in the Hangzhou region.
        auth = oss2.Auth('')
        bucket = oss2.Bucket(auth, endpoint, 'wenchou')
        key = filename
        bucket.put_object_from_file(key, filepath)
        return ['https://wenchou.oss-rg-china-mainland.aliyuncs.com/' + filename]
        # // https://wenchou.oss-rg-china-mainland.aliyuncs.com/test.docx
