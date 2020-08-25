from PIL import Image     
import os       
path = r'/home/ahmad/Desktop/ObjectDetection/tensorflow/workspace/training/images/train/' 
i = 0
for file in os.listdir(path):      
    extension = file.split('.')[-1]
    try:
        if extension != 'xml':
            fileLoc = os.path.join(path,file)
            img = Image.open(fileLoc)
            i += 1
            if img.mode != 'RGB':
                  print(file+', '+img.mode)
    except  Exception as e:
        print(str(e))
print(i)