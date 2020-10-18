# 保存上传图片path: Upload_Image

# 输出测试图片path：Output_Image

# 上传后自动测试图片pyFile: FaceMaskDetection/pytorch_test.py

#pyFile新添加代码标注comment:(example)
``` python
    # A1 codes starts
    f = open("tmp/img_info.txt", "a")
    f.write(", ".join(map(str,output_info))+'\n')
    f.close()
    # A1 codes ends
```    

**(目前的问题是fileupload.py最后return的testImgName无法在网页上显示)**