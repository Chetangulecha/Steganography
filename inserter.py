# Using wave to read wav file
import wave
import random
import src.steganography.audio.lsb.tools as tools

class MessageInserter:
    # Read bytes per frame
    def read_frame_file(self, filename,is_mono):
        song = wave.open(filename, mode='rb')
        frame_bytes = bytearray(list(song.readframes(song.getnframes())))
        if not is_mono:
            frame_bytes = tools.split_array(frame_bytes,4)
        song.close()
        return frame_bytes
    
    # Get song params
    def get_params (self, filename):
        song = wave.open(filename, mode='rb')
        params = song.getparams()
        song.close()
        return params
    
    # Read included message file
    def read_files(self, file):
        is_ext = file.split("/")[-1].find(".") != -1
        if is_ext:
            ext = file.split(".")[-1]
        else:
            ext = ""
        with open(file, "rb") as f:
            byte_file = f.read()
        return (byte_file, ext)

    # Insert message
    def insert_message(self, extension, message, frame, key, is_mono, lsb_bit_mode=1, encrypted=False, randomize_bytes=False, randomize_frames=False):
        if not self.check_payload(message, frame, is_mono):
            print("Size of information exceeded")
            return
        len_message = str(len(message))
        string = len_message + '#' + extension + '#' + message
        key = key.upper()
        seed = 0
        for i in key:
            seed += ord(i)
        
        # Give sign if encrypted
        if encrypted:
            if is_mono:
                frame[0] = frame[0] & 254 | 1
            else:
                frame[0][0] = frame[0][0] & 254 | 1
            # encrypt string with key
            string = tools.vigenere_extended(string, key)
        else:
            if is_mono:
                frame[0] = frame[0] & 254 | 0
            else:
                frame[0][0] = frame[0][0] & 254 | 0
        

        # Convert text to bit array
        bits = list(map(int, ''.join([bin(ord(i)).lstrip('0b').rjust(8,'0') for i in string])))

        if randomize_frames:
            if is_mono:
                frame[1] = frame[1] & 254 | 1
            else:
                frame[0][1] = frame[0][1] & 254 | 1
            random.seed(seed)
            frame_list = list(range(len(frame)))
            random.shuffle(frame_list)
        else:
            if is_mono:
                frame[1] = frame[1] & 254 | 0
            else:
                frame [0][1] = frame[0][1] & 254 | 0
            frame_list = list(range(len(frame)))
        
        if randomize_bytes:
            if is_mono:
                frame[2] = frame[2] & 254 | 1
            else:
                frame[0][2] = frame[0][2] & 254 | 1
                bytes_list = list(range(len(frame[0])))
                random.seed(seed)
                random.shuffle(bytes_list)
        else:
            if is_mono:
                frame[2] = frame[2] & 254 | 0
            else:
                frame[0][2] = frame[0][2] & 254 | 0
                bytes_list = list(range(len(frame[0])))
        
        index = 0
        if lsb_bit_mode==2:
            if is_mono:
                frame[3] = frame[3] & 254 | 1
                for i in frame_list:
                    if index >= len(bits):
                        break
                    if i >= 4:
                        frame[i] = frame[i] & 252 | (2*bits[index] + bits[index+1])
                        index += 2
            else:
                frame[0][3] = frame[0][3] & 254 | 1
                for i in frame_list:
                    for j in bytes_list:
                        if index >= len(bits):
                            break
                        if i != 0:
                            frame[i][j] = frame[i][j] & 252 | (2*bits[index] + bits[index+1])
                            index += 2
        else:
            if is_mono:
                frame[3] = frame[3] & 254 | 0
                for i in frame_list:
                    if index >= len(bits):
                        break
                    if i >= 4:
                        frame[i] = frame[i] & 254 | bits[index]
                        index+=1
            else:
                frame[0][3] = frame[0][3] & 254 | 0
                for i in frame_list:
                    for j in bytes_list:
                        if index >= len(bits):
                            break
                        if i != 0:
                            frame[i][j] = frame[i][j] & 254 | bits[index]
                            index+=1

        frame_modified = bytes()
        merged_array = bytearray()

        if is_mono:
            merged_array = frame
        else:
            for i in frame:
                merged_array += i

        # Convert to bytes
        frame_modified += bytes(merged_array)
        return frame_modified

    # Write bytes to a new wave audio file
    def write_file(self, filename, frame, params):
        with wave.open(filename, 'wb') as fd:
            fd.setparams(params)
            fd.writeframes(frame)

    # Check payload size
    def check_payload(self, message, frame_bytes, is_mono):
        k = (1 if is_mono else 4)
        max_size = len(frame_bytes) * k
        #print('Max size : {}'.format(max_size))
        ok = False if len(message) > max_size else True
        return ok
