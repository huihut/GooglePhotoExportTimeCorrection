# -*- coding: utf-8 -*-
"""

Created by huihut
Reference link: https://www.yetanotherdatablog.com/blogposts/googlephotostakeout/googlephotostakeout.html

"""
import json
import os
import glob
import re
from fractions import Fraction
import piexif
from datetime import datetime


def get_tuples(combined):
    return [(item.numerator, item.denominator) for item in combined]


# GPS
def geo_degrees_conv(degrees):
    is_positive = degrees >= 0
    degrees = abs(degrees)
    minutes, seconds = divmod(degrees * 3600, 60)
    seconds = round(seconds, 2)
    degrees, minutes = divmod(minutes, 60)
    degrees = degrees if is_positive else -degrees
    degrees2 = Fraction(degrees).limit_denominator(1000)
    minutes = Fraction(minutes).limit_denominator(1000)
    seconds = Fraction(seconds).limit_denominator(1000)
    combined = [degrees2, minutes, seconds]
    combined = get_tuples(combined)
    return combined


# get picture filename
def get_picture_names(json_filename):
    jpg_filename_stemmed = json_filename.replace('.json', '')
    jpg_filename_stemmed = json_filename.replace('.jpg', '')
    all_files = glob.glob(jpg_filename_stemmed + '*')
    only_pictures = [x for x in all_files if ".json" not in x]
    return only_pictures


# modify exif photoTakenTime, GPS
def modify_exif(exif_dict, filename, json_data):  # input1: exif dictionary, input2: the filename, input3: the json data
    # datatime taken
    photo_date = float(json_data['photoTakenTime']['timestamp'])
    photo_date = datetime.fromtimestamp(photo_date)
    photo_date = photo_date.strftime("%Y:%m:%d %H:%M:%S")
    try:
        original_datetime = exif_dict['Exif'][36867]  # if the JPG had a value, get it
    except:
        original_datetime = '0:0:0 0:0:0'  # no EXIF information in the JPG
    exif_dict['Exif'][36867] = photo_date  # write the json data to the EXIF dictionary
    print('json_file:', json_data['title'], 'picture:', filename, 'date stored in exif was:', original_datetime,
          'and is changed to:', photo_date)
    # geo data
    exif_dict['GPS'][piexif.GPSIFD.GPSLatitude] = geo_degrees_conv(
        json_data['geoData']['latitude'])  # write the latitude information from the JSON to the EXIF dictionary
    exif_dict['GPS'][piexif.GPSIFD.GPSLongitude] = geo_degrees_conv(
        json_data['geoData']['longitude'])  # write the longitude information from the JSON to the EXIF dictionary
    print('json_file:', json_data['title'], 'picture:', filename, 'latitude set to:',
          exif_dict['GPS'][piexif.GPSIFD.GPSLatitude],
          'longitude set to:', exif_dict['GPS'][piexif.GPSIFD.GPSLongitude])
    return exif_dict  # return the exif dictionary to main


# modify photoLastModifiedTime
def modify_time(filename, json_data):
    photo_date = float(json_data['photoLastModifiedTime']['timestamp'])
    os.utime(filename, (photo_date, photo_date))


if __name__ == '__main__':
    path = input('Please enter the path of the Google Photo Takeout directory:')
    path = re.sub('\\\\', '/', path)
    os.chdir(path)

    json_files = [pos_json for pos_json in os.listdir(path) if pos_json.endswith('.json')]
    for js in json_files:
        with open(os.path.join(path, js), 'r', encoding='UTF-8') as json_file:
            json_data = json.load(json_file)  # load each json file data
        picture_names = get_picture_names(json_data['title'])  # get the names of the jpgs from the json file
        for i in picture_names:  # iterate over each picture
            try:
                modify_time(path + '/' + i, json_data)  # photoLastModifiedTime
            except:
                print('modify_time error: ' + i)
            try:
                exif_dict = piexif.load(i)  # load the EXIF metadata
                exif_dict = modify_exif(exif_dict, i, json_data)  # update the EXIF metadata
                exif_bytes = piexif.dump(exif_dict)
                piexif.insert(exif_bytes, i)  # write the new EXIF metadata to the jpg file
            except:
                print('piexif error: ' + i)
