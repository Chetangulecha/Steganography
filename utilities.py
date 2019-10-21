import math
import os
import random
import shutil
from getmotionvector import MotionVector
import cv2
import numpy as np
from contextlib import suppress
import io
import sys


def vigenere_encrypt(message, key) :
	return(message)

def video_to_image(path, temp_folder) :
	try :
		os.mkdir(temp_folder)
	except OSError:
		remove(temp_folder)
		os.mkdir(temp_folder)

	count = 0

	success = True

	vidcap = cv2.VideoCapture(path)
	info_image = {}
	info_image['width'] = int(vidcap.get(3))
	info_image['height'] = int(vidcap.get(4))
	#ret = vidcap.set(5, 10)
	info_image['fps'] = int(vidcap.get(5))
	print ("FPS = ", info_image['fps'])
	print ("Frame width = ", info_image['width'])
	print ("Frame height = ", info_image['height'])
	#info_image['fps'] = 5 
	info_image['fourcc'] = int(vidcap.get(6))
	while success:
		success,image = vidcap.read()
		if (success) :
			cv2.imwrite(os.path.join(temp_folder, "{:d}.png".format(count)), image)
			count += 1

	info_image['total_image'] = count
	print ("Total frames = ", info_image['total_image'])	
	return(info_image)

def remove(path):
  if os.path.isfile(path):
      os.remove(path)
  elif os.path.isdir(path):
      shutil.rmtree(path)
  else:
      raise ValueError("file {} is not a file or dir.".format(path))

with suppress(Exception):
	def generate_random_order_pixel(video_name, image_width, image_height, seed, need_pixel, need_frame, frame_sequencial, pixel_sequencial, pixel_range, frame_range, pixel_per_image,is_motion) :
		# create a text trap and redirect stdout
		text_trap = io.StringIO()
		sys.stdout = text_trap
		
		random.seed(seed)
		#pixel_order = np.array([])
		pixel_order = []
		if(is_motion):
			i = 0
			counter = 0
			try:
				array = MotionVector(video_name)
			#print (array)
			except Exception:
				pass
			while (counter <= need_pixel):
		
				current_frame = array[i][0]
				#print(current_frame)
				xcor = array[i][1]
				ycor = array[i][2]
				wlim = array[i][3]
				hlim = array[i][4]
				x = xcor
				y = ycor
				while(1) :
					val = x*image_width + y + current_frame * pixel_per_image 
					pixel_order.append(val)
					counter = counter + 1
					if (counter > need_pixel):
						break
					if(y < ycor + wlim):
						y = y + 1
					elif(x < xcor + hlim):
						y = ycor
						x = x + 1
					else:
						i = i + 1
						break
		elif ((not frame_sequencial) and (not pixel_sequencial)) :
			pixel_order = random.sample(range(pixel_range[0],pixel_range[1]), need_pixel)
		elif (pixel_sequencial and frame_sequencial) :
			pixel_order = list(range (0, need_pixel))
		elif (pixel_sequencial and (not frame_sequencial)) :
			frame_order = random.sample(range(frame_range[0],frame_range[1]), need_frame)
			for frame_idx in frame_order :
				pixel_in_frame = list(range (frame_idx * pixel_per_image, (frame_idx+1) * pixel_per_image))
				pixel_order = np.append(pixel_order, pixel_in_frame)
			pixel_order = pixel_order[:need_pixel]
		elif (not(pixel_sequencial) and frame_sequencial) :
			frame_order = list(range (0,need_frame))
			for frame_idx in frame_order :
				# print(frame_idx)
				pixel_in_frame = random.sample(range(frame_idx * pixel_per_image, (frame_idx+1) * pixel_per_image), pixel_per_image)
				pixel_order = np.append(pixel_order, pixel_in_frame)
			pixel_order = pixel_order[:need_pixel]
	
		#pixel_order = np.array([])
	
		#flag_motion_vector = 1
		#print (need_pixel)
		sys.stdout = sys.__stdout__
		#print (pixel_order)
		return (pixel_order)
