import wave
import random
import base64
import src.steganography.audio.lsb.tools as tools

class MessageExtractor:
    # Read encrypted file as bytes
    def read_encrypted_file(self, filename):
        song = wave.open(filename, mode='rb')
        frame_bytes = bytearray(list(song.readframes(song.getnframes())))
        return frame_bytes
    
    # Get LSB from file in string format
    def get_lsb(self, frame_bytes,key,is_mono):
        
        # Get sign from LSB
        encrypted = bin(frame_bytes[0])[-1] == '1'
        random_frames = bin(frame_bytes[1])[-1] == '1'
        random_bytes = bin(frame_bytes[2])[-1] == '1'

        # Opt is sign for amount of LSB that used
        opt = 2 if bin(frame_bytes[3])[-1] == '1' else 1

        index = 0 
        temp = ""
        string = ""
        key = key.upper()
        seed = 0
        for i in key:
            seed += ord(i)

        # Extract the LSB of each byte
        if opt==1:
            mod_index = 8
            extracted = [frame_bytes[i] & 1 for i in range(len(frame_bytes))]
            if not is_mono:
                extracted = tools.split_array(extracted, 4)

        # Extract the 2 LSB of each byte
        if opt==2:
            mod_index = 4
            extracted = [bin(frame_bytes[i] & 3).lstrip('0b').rjust(2,'0') for i in range(len(frame_bytes))]
            if not is_mono:
                extracted = tools.split_array(extracted, 4)

        # Handling random frame case
        if random_frames:
            random.seed(seed)
            frame_list = list(range(len(extracted)))
            random.shuffle(frame_list)
        else:
            frame_list = range(len(extracted))

        # Handling random bytes case
        if random_bytes:
            random.seed(seed)
            byte_list = list(range(len(extracted[0])))
            random.shuffle(byte_list)
        else:
            if not is_mono:
                byte_list = range(len(extracted[0]))

        # Get all in string format
        if is_mono:
            for i in frame_list:
                if i>=4:
                    if index % mod_index != (mod_index - 1):
                        temp += str(extracted[i])
                    else:
                        temp += str(extracted[i])
                        string += chr(int(temp,2))
                        temp = ""
                    index += 1
        else:
            for i in frame_list:
                for j in byte_list:
                    if i!=0:
                        if index % mod_index != (mod_index - 1):
                            temp += str(extracted[i][j])
                        else:
                            temp += str(extracted[i][j])
                            string += chr(int(temp,2))
                            temp = ""
                        index += 1
        
        # Decrypt if needed
        if encrypted:
            string = tools.vigenere_extended_decryption(string,key)
        return string

    # Get the sign of message in audio (length, extension)
    def get_info_message(self, string):
        length = ""
        extension = ""
        i = 0

        while string[i] != '#':
            length += string[i]
            i += 1

        i+=1
        while string[i] != '#':
            extension += string[i]
            i += 1

        return (int(length), extension)
    
    # Print the message inside file
    def write_secret_message(self, length, ext, string, outputname):
        init = len(str(length)) + len(str(ext)) + 2 #Get init index
        decoded = string[init:init+length]

        # Convert to bytes
        bytes_file = decoded.encode('utf-8')
        bytes_file = base64.b64decode(bytes_file)
        
        with open(outputname, 'wb') as fd:
            fd.write(bytes_file)

