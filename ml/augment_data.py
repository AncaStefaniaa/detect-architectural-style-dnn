from PIL import Image
import random
import os

# The percentage of the an original image's height and width to use for random crops.
PERCENTAGE = 0.50
input_dir = './splitted_dataset_90_0_10'
output_dir = './augmented_8_splitted_dataset_90_0_10'

def rand_crop(filepath):
    image = Image.open(filepath)

    # treats the png format photos
    if image.mode != 'RGB':
        image = image.convert('RGB')

    width, height = image.size
    crop_width = int(width * PERCENTAGE)
    crop_height = int(height * PERCENTAGE)

    # Choose a random point for the top left corner of the new crop.
    tl_x = random.randint(0, crop_width)
    tl_y = random.randint(0, crop_height)

    coords = (tl_x, tl_y, tl_x + crop_width, tl_y + crop_height)
    return image.crop(coords)


def rotate(filepath, angle):
    image = Image.open(filepath)

    if image.mode != 'RGB':
        image = image.convert('RGB')

    return image.rotate(angle)


def flip(filepath):
    image = Image.open(filepath)

    if image.mode != 'RGB':
        image = image.convert('RGB')

    return image.transpose(Image.FLIP_LEFT_RIGHT)


def augment_image(filepath):
    splitted_path = filepath.split('\\')
    new_folder = splitted_path[-3] + '\\' + splitted_path[-2]
    filename_without_ext = splitted_path[-1].split('.')[0]

    resulted_dir = os.path.join(output_dir, new_folder)

    original = Image.open(filepath)

    if original.mode != 'RGB':
        original = original.convert('RGB')

    flipped = flip(filepath)

    rotated = []
    # for angle in [-15, -5, 5, 15]:
    for angle in [-10, 5, 10]:
        rotated.append(rotate(filepath, angle))

    cropped = []
    for i in range(3):
        cropped.append(rand_crop(filepath))

    totals = [original] + [flipped] + rotated + cropped
    for idx, img in enumerate(totals):
        out_filename = "%s-%d.jpg" % (filename_without_ext, idx)
        out_full_path = os.path.join(resulted_dir, out_filename)
        img.save(out_full_path)

total = 0
for root, dirs, files in os.walk(input_dir):
    total += len(files)

cnt = 0
for root, dirs, files in os.walk(input_dir):
    for dir in dirs:
        dir_path = os.path.join(root, dir)

        if len(dir_path.split('\\')) > 2:
            continue

        for root2, dirs2, files2 in os.walk(dir_path):
            for dir2 in dirs2:
                dir_path2 = os.path.join(root2, dir2)

                new_dir_path = os.path.join(output_dir, dir, dir2)
                os.mkdir(new_dir_path)

                for root3, dir3, files3 in os.walk(dir_path2):
                    for file in files3:
                        img_path = os.path.join(root3, file)
                        augment_image(img_path)
                        
                        cnt += 1
                        print ('Processed %d images - %.2f%%' % (cnt, (100.00000 * cnt / total)), end='\r')
