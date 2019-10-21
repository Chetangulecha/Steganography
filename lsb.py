import shutil
import cv2
import math
import os
from subprocess import call,STDOUT

import numpy as np
import src.steganography.video.utilities as utils
import src.utilities.ext_vigenere as vig_cipher
import src.utilities.cipher_utils as vig_utils

BYTE_PER_PIXEL = 3
HIDE_TEMP_FOLDER = 'steganography_temp'
HIDE_OUTPUT_FOLDER = 'steganography_output'
EXTRACT_TEMP_FOLDER = 'steganoanalysis_temp'
EXTRACT_OUTPUT_FOLDER = 'steganoanalysis_output'
AUDIO_TEMP_FOLDER = 'audio_temp'

def hide_secret(cover_video_dir, secret_msg_dir, key, output_file_name, lsm_byte, is_seq_frame=True, is_seq_pixel=True, is_encrypted=False,is_motion=False):
  # Load the cover video

  #extractiong image
  info_image = utils.video_to_image(cover_video_dir, HIDE_TEMP_FOLDER)

  #extraction audio
  try :
    os.mkdir(AUDIO_TEMP_FOLDER)
  except OSError:
    utils.remove(AUDIO_TEMP_FOLDER)
    os.mkdir(AUDIO_TEMP_FOLDER)
  audio_file = AUDIO_TEMP_FOLDER + '/audio.wav'
  call(["ffmpeg", "-i", str(cover_video_dir), "-q:a", "0", "-map", "a", audio_file, "-y"],stdout=open(os.devnull, "w"), stderr=STDOUT)

  # Read the extension of secret message
  message_extension = ''
  for character_idx in range (len(secret_msg_dir)-1, -1, -1) :
    if (secret_msg_dir[character_idx] == '.') :
      break
    message_extension = secret_msg_dir[character_idx] + message_extension
    if (character_idx == 0) :
      message_extension = ''
      break
  # Load the secret message
  ord_bytes = []
  message = ''
  with open(secret_msg_dir, "rb") as input:
    while True :
      word = input.read(1)
      if (word == b'') :
        break
      ord_bytes.append(word)
      message = message + chr(ord(word))
  message_in_bytes = ''.join('{0:08b}'.format(ord(x)) for x in ord_bytes)

  len_message = len(message_in_bytes)
  extra_message = str(int(is_encrypted)) + str(len_message) + '|' + message_extension + '|'
  # print(extra_message)
  extra_message = ''.join('{0:08b}'.format(ord(x)) for x in extra_message)

  message_in_bytes = extra_message + message_in_bytes

  # Generate seed from key
  seed_from_key = generate_seed(key)

  # Configuration setting
  image_index = 0
  save_config(image_index, is_seq_frame, is_seq_pixel, lsm_byte, HIDE_TEMP_FOLDER)

  # Message size validation
  max_information_per_image = info_image['width'] * info_image['height'] * BYTE_PER_PIXEL * lsm_byte
  is_msg_too_long = (max_information_per_image * info_image['total_image']) < len(message_in_bytes)
  if (is_msg_too_long) :
    print('message too long')
    return {'result': 'failed'}
  
  # Checking execution requirements
  required_pixel_count = math.ceil(len(message_in_bytes) / (BYTE_PER_PIXEL * lsm_byte))
  required_frame_count = math.ceil(required_pixel_count / (info_image['width'] * info_image['height']))
  required_pixel_count = int(required_pixel_count)
  required_frame_count = int(required_frame_count)
  pixel_range = (0, info_image['width']*info_image['height']*info_image['total_image'])
  frame_range = (0, info_image['total_image'])
  pixel_per_image = info_image['width'] * info_image['height']
  
  pixel_order = utils.generate_random_order_pixel(
    cover_video_dir,
    info_image['width'],
    info_image['height'],
    seed_from_key,
    required_pixel_count,
    required_frame_count,
    is_seq_frame,
    is_seq_pixel,
    pixel_range,
    frame_range,
    pixel_per_image,
    is_motion
  )

  # Start steganography process
  psnr = apply_steganography(info_image, pixel_order, message_in_bytes, BYTE_PER_PIXEL, lsm_byte, HIDE_TEMP_FOLDER)
  print("PSNR = ", psnr)
  try :
    os.mkdir(HIDE_OUTPUT_FOLDER)
  except OSError:
    utils.remove(HIDE_OUTPUT_FOLDER)
    os.mkdir(HIDE_OUTPUT_FOLDER)
  if len(os.listdir(AUDIO_TEMP_FOLDER)) != 0:
    call(["ffmpeg", "-i", "{}/%d.png".format(HIDE_TEMP_FOLDER), "-r", str(info_image['fps']), "-i", audio_file, "-vcodec", "png", "{}/{}".format(HIDE_OUTPUT_FOLDER, output_file_name), "-y"],stdout=open(os.devnull, "w"), stderr=STDOUT)
  else :
    call(["ffmpeg", "-i", "{}/%d.png".format(HIDE_TEMP_FOLDER), "-r", str(info_image['fps']), "-vcodec", "png", "{}/{}".format(HIDE_OUTPUT_FOLDER, output_file_name), "-y"],stdout=open(os.devnull, "w"), stderr=STDOUT)
  # call(["ffmpeg", "-i", "{}/temp.avi".format(HIDE_TEMP_FOLDER), "-i", audio_file,  "{}/{}".format(HIDE_OUTPUT_FOLDER, output_file_name), "-vcodec", "copy", "-y"],stdout=open(os.devnull, "w"), stderr=STDOUT)
  
  #utils.remove(HIDE_TEMP_FOLDER)
  #utils.remove(AUDIO_TEMP_FOLDER)

  output_result = {
    'psnr' : '{}'.format(psnr),
    'result': 'success',
    'output_dir': '{}/{}/{}'.format(os.getcwd(), HIDE_OUTPUT_FOLDER, output_file_name)
  }
  return output_result

def extract_secret(stegano_video_dir, key, output_file_name,is_motion):
  info_image = utils.video_to_image(stegano_video_dir, EXTRACT_TEMP_FOLDER)
  image_index = 0
  is_seq_frame, is_seq_pixel, lsm_byte = extract_config(image_index, EXTRACT_TEMP_FOLDER)
  seed_from_key = generate_seed(key)
  #print(is_seq_frame, is_seq_pixel, lsm_byte)
  need_pixel = 240
  need_frame = math.ceil(need_pixel / (info_image['width'] * info_image['height']))
  pixel_range = (0, info_image['width']*info_image['height']*info_image['total_image'])
  frame_range = (0, info_image['total_image'])
  pixel_per_image = info_image['width'] * info_image['height']
  need_pixel = int(need_pixel)
  need_frame = int(need_frame)
  #is_motion=False
  pixel_order = utils.generate_random_order_pixel(stegano_video_dir,info_image['width'],info_image['height'],seed_from_key, need_pixel, need_frame, is_seq_frame, is_seq_pixel, pixel_range, frame_range, pixel_per_image,is_motion)
  is_encrypted, len_message, len_total_message, extension, range_message = get_extension_len_message(info_image, pixel_order, BYTE_PER_PIXEL, lsm_byte, EXTRACT_TEMP_FOLDER)
  need_pixel = math.ceil(len_total_message / (BYTE_PER_PIXEL * lsm_byte))
  
  pixel_order = utils.generate_random_order_pixel(stegano_video_dir,info_image['width'],info_image['height'],seed_from_key, need_pixel, need_frame, is_seq_frame, is_seq_pixel, pixel_range, frame_range, pixel_per_image,is_motion)
  pixel_order = np.array(pixel_order)
  message = apply_steganoanalytic(info_image, pixel_order, BYTE_PER_PIXEL, lsm_byte, range_message, EXTRACT_TEMP_FOLDER)

  # if is_encrypted:
  #     message = vig_cipher.ExtendedVigenere().decipher(message, key)
  print('Is encrypted: {}'.format(is_encrypted))
  temp_msg_name = 'vid_temp_dec'
  if (extension == 'plain') :
    plain = ''
    for i in range (0,len(message) // 8) :
      a = message[i*8:i*8 + 8]
      x = int(a, 2)
      plain = plain + chr(x)
    #print(plain)
  else :
    plain = []
    for i in range (0,len(message) // 8) :
      a = message[i*8:i*8 + 8]
      plain.append(int(a, 2))
    if extension != '':
      output_file_name += '.' + extension
      temp_msg_name += '.' + extension
    if (is_encrypted):
      print('extension: {}'.format(extension))
      print(output_file_name)
      print(temp_msg_name)
      with open(temp_msg_name,'wb') as f:
        f.write(bytearray(plain))
      encrypted_secret_message = vig_utils.read_input_bytes(temp_msg_name)
      real_secret_message = vig_cipher.ExtendedVigenere().decipher(encrypted_secret_message, key)
      vig_utils.save_output_bytes(real_secret_message, output_file_name)
      # os.remove(temp_msg_name)
    else:
      with open(output_file_name, 'wb') as f:
        f.write(bytearray(plain))
  utils.remove(EXTRACT_TEMP_FOLDER)
  
  output_result = {
    'result' : 'success',
    'output_dir' : '{}/{}'.format(os.getcwd(), output_file_name),
  }
  return output_result

def generate_seed(key):
  seed_from_key = 0
  for i in key:
    seed_from_key += ord(i)
  return seed_from_key

def apply_steganography(info_image, pixel_order, byte_message, byte_per_pixel, lsm_byte, temp_folder) :
  rms = 0
  changed_img = set([])
  for message_idx in range (0, len(byte_message),lsm_byte*byte_per_pixel) :
    # print(message_idx)
    message = ''
    byte_idx = pixel_order[int(message_idx/(lsm_byte*byte_per_pixel))]
    for idx in range (message_idx, message_idx+(lsm_byte*byte_per_pixel)) :
      if (idx < len(byte_message)) :
        message = message + str(byte_message[idx])
      else :
        message = message + str('0')
    
    pixel_each_img = info_image['width']*info_image['height']
    img_idx = byte_idx // pixel_each_img
    height_img = (byte_idx % pixel_each_img) // (info_image['width'])
    width_img = (byte_idx % pixel_each_img) % (info_image['width'])
    img_idx = int(img_idx)
    height_img = int(height_img)
    width_img = int(width_img)
    changed_img.add(img_idx)
    delta_intensity = change_lsb(img_idx, height_img, width_img, message, byte_per_pixel, lsm_byte, temp_folder)
    rms += delta_intensity
  rms = math.sqrt(rms/(len(changed_img) * info_image['width'] * info_image['height']))
  psnr = 20 * math.log10(256/rms)
  # rms_point = rms_point / 
  return (psnr)

def change_lsb(image_index, height_img, width_img, byte_message, byte_per_pixel, lsm_byte, temp_folder) :
  image = cv2.imread(temp_folder + "/" + str(image_index) + ".png", 1 )
  int_lsb = image[height_img, width_img]
  init_int_lsb = int_lsb
  byte_lsb = ['{0:08b}'.format(x) for x in int_lsb]
  for byte in range (0, byte_per_pixel) :
    byte_lsb[byte] = (byte_lsb[byte])[:-1*(lsm_byte)]
    byte_lsb[byte] = byte_lsb[byte] + byte_message[:lsm_byte]
    byte_message = byte_message[lsm_byte:]
  int_lsb = tuple([int(x, 2) for x in byte_lsb])
  delta_intensity = 0
  intensity_after = 0
  intensity_before = 0
  for rgb_idx in range (0, len(int_lsb)) :
    intensity_after += int_lsb[rgb_idx]
    intensity_before += init_int_lsb[rgb_idx]
  delta_intensity = ((intensity_after/3) - (intensity_before/3))**2
  image[height_img, width_img] = int_lsb
  cv2.imwrite(temp_folder + "/" + str(image_index) + ".png",image)
  return(delta_intensity)

def apply_steganoanalytic(info_image, pixel_order, byte_per_pixel, lsm_byte, range_message, temp_folder) :
  message = ''
  for message_idx in range (0, len(pixel_order)*lsm_byte*byte_per_pixel,lsm_byte*byte_per_pixel) :
    byte_idx = pixel_order[int(message_idx/(lsm_byte*byte_per_pixel))]		
    pixel_each_img = info_image['width']*info_image['height']
    img_idx = byte_idx // pixel_each_img
    height_img = (byte_idx % pixel_each_img) // (info_image['width'])
    width_img = (byte_idx % pixel_each_img) % (info_image['width'])
    message = message + extract_lsb(img_idx, height_img, width_img, byte_per_pixel, lsm_byte, temp_folder)

  return(message[range_message[0]:range_message[1]])

def extract_lsb(image_index, height_img, width_img, byte_per_pixel, lsm_byte, temp_folder) :
  image = cv2.imread(temp_folder + "/" + str(int(image_index)) + ".png", 1 )
  int_lsb = image[int(height_img), int(width_img)]
  message = ''
  byte_lsb = ['{0:08b}'.format(x) for x in int_lsb]
  for byte in range (0, byte_per_pixel) :
    message += (byte_lsb[byte])[-1*(lsm_byte):]
  return(message)

def get_extension_len_message(info_image, pixel_order, byte_per_pixel, lsm_byte, temp_folder) :
  message = ''
  is_len = True
  is_extension = False
  extension = ''
  len_message = 0
  xi = 1
  len_total_message = 0
  extension_idx = 0
  for message_idx in range (0, len(pixel_order)*lsm_byte*byte_per_pixel,lsm_byte*byte_per_pixel) :
    byte_idx = pixel_order[int(message_idx/(lsm_byte*byte_per_pixel))]    
    pixel_each_img = info_image['width']*info_image['height']
    img_idx = byte_idx // pixel_each_img
    height_img = (byte_idx % pixel_each_img) // (info_image['width'])
    width_img = (byte_idx % pixel_each_img) % (info_image['width'])
    message = message + extract_lsb(img_idx, height_img, width_img, byte_per_pixel, lsm_byte, temp_folder)
    range_message = (0, 0)
    if (len(message) // 8 == xi) :
      xi += 1
      plain = ''
      for i in range (0,len(message) // 8) :
        a = message[i*8:i*8 + 8]
        x = int(a, 2)
        plain = plain + chr(x)
      if (plain[-1] == '|') :
        if (is_extension) :
          extension = plain[extension_idx:-1]
          extension_idx = len(plain)
          is_extension = False
          len_total_message = len(plain) * 8 + len_message
        if (is_len) :
          is_encrypted = (int(plain[0]) == 1)
          len_message = int(plain[1:-1])
          extension_idx = len(plain)
          is_len = False
          is_extension = True
    if (not(is_extension) and not(is_len)) :
      range_message = (extension_idx*8, (extension_idx*8)+len_message)
      break
  #is_motion = True
  #print (plain) 
  return(is_encrypted, len_message, len_total_message, extension, range_message)

def extract_config(image_index, temp_folder) :
  image = cv2.imread(temp_folder + "/" + str(image_index) + ".png", 1 )
  int_lsb = image[0,0]
  byte_lsb = ['{0:08b}'.format(x) for x in int_lsb]
  frame_sequencial = (str(byte_lsb[0])[-3] == '1')
  pixel_sequencial = (str(byte_lsb[1])[-3] == '1')
  lsm_byte = int(str((byte_lsb[2])[-3])) + 1
  return(frame_sequencial, pixel_sequencial, lsm_byte)

def save_config(image_index, frame_sequencial, pixel_sequencial, lsm_byte, temp_folder) :
  image = cv2.imread(temp_folder + "/" + str(image_index) + ".png", 1 )
  int_lsb = image[0,0]
  byte_lsb = ['{0:08b}'.format(x) for x in int_lsb]
  
  third_byte = byte_lsb[0][-2:]
  byte_lsb[0] = byte_lsb[0][:-3]
  if (frame_sequencial) :
    byte_lsb[0] = byte_lsb[0] + '1' + third_byte
  else :
    byte_lsb[0] = byte_lsb[0] + '0' + third_byte
  
  third_byte = byte_lsb[1][-2:]
  byte_lsb[1] = byte_lsb[1][:-3]
  if (pixel_sequencial) :
    byte_lsb[1] = byte_lsb[1] + '1' + third_byte
  else :
    byte_lsb[1] = byte_lsb[1] + '0' + third_byte
  
  third_byte = byte_lsb[2][-2:]
  byte_lsb[2] = byte_lsb[2][:-3]
  if (lsm_byte == 2) :
    byte_lsb[2] = byte_lsb[2] + '1' + third_byte
  else :
    byte_lsb[2] = byte_lsb[2] + '0' + third_byte


  int_lsb = tuple([int(x, 2) for x in byte_lsb])

  
  image[0,0] = int_lsb
  cv2.imwrite(temp_folder + "/" + str(image_index) + ".png",image)
