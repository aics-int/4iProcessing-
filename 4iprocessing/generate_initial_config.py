

# pdir = r'\\allen\aics\microscopy\Antoine\Analyse EMT\4i Data\5500000724\ZSD1'
import os
from pathlib import Path
import re
from aicsimageio import AICSImage
import argparse
import json

# run this to make the initial yaml files and then edit those files to make sure nothing is missing.
# this code only helps make the yaml files...it does not generate a perfect yaml automatically. 

parser = argparse.ArgumentParser()
parser.add_argument('--input_dirs', type=str, default=["/allen/aics/microscopy/Antoine/Analyse EMT/4i Data/5500000733","/allen/aics/microscopy/Antoine/Analyse EMT/4i Data/5500000724", "/allen/aics/microscopy/Antoine/Analyse EMT/4i Data/5500000728", "/allen/aics/microscopy/Antoine/Analyse EMT/4i Data/5500000726", "/allen/aics/microscopy/Antoine/Analyse EMT/4i Data/5500000725"], help="input dirs to parse")
parser.add_argument('--output_path', type=str, required=True, help="final alignment outputs to specify in yaml file")
parser.add_argument('--output_yaml_dir', type=str, required=True, help="final alignment outputs to specify in yaml file")


def sort_rounds(rounds):
    # function to sort rounds
    Orginal_numbered_list = []
    for i in range(len(rounds)):
        int(re.search(r'\d+', rounds[i]).group())
        Orginal_numbered_list.append(int(re.search(r'\d+', rounds[i]).group()))
    sorted_list = sorted(Orginal_numbered_list)
    final_sorted_list=[]
    for num in sorted_list:
        index = Orginal_numbered_list.index(num)
        final_sorted_list.append(rounds[index])
    #print(final_sorted_list)
    return final_sorted_list


if __name__ == '__main__':
    args= parser.parse_args()

    for bdir in args.input_dirs:
        barcode = Path(Path(bdir)).name
        print(barcode)
        config ={}
        config['Data']=[]
        scope_list = [x for x in os.listdir(bdir) if 'ZSD' in x]
        for scope in scope_list:
            pdir = bdir + os.sep + scope
            #round_list = [x for x in os.listdir(pdir) if bool(re.search('Time|Round [0-9]+(?!.)',x,re.IGNORECASE))&(Path(x).stem==Path(x).name)]
            round_list = [x for x in os.listdir(pdir) if bool(re.search('Time|Round [0-9]+',x,re.IGNORECASE))&(Path(x).stem==Path(x).name)]
            #round_list.sort(key=int)
            round_list = sort_rounds(round_list)

            print("round list is {}".format(round_list))

            for round_num in round_list:
                ppath = os.path.join(pdir, round_num)
                czi_list = [x for x in os.listdir(ppath) if ('.czi' in x)&bool(re.search('20x',x,re.IGNORECASE))]
                # print(czi_list)
                # subd = {}
                # subd['name'] = round_num
                # subd['details'] = []

                for czi_name in czi_list:
                    fpath = os.path.join(ppath,czi_name)
                    fpathr = fpath.replace(os.sep,'/')
                    fpath2 ='"'+fpathr+'"'
                    fpath2 = fpathr
                    fpath = fpath2.replace("'",'')

                    # each round of imaging is a multi-scene file like with dimensions STCZYX (only "time lapse rounds" have T>1). All rounds have S>1 and T>1
                    # define the location of the reference channel in the list of channels
                    # ideally the reference channel will be the image containing the nuclear fluorescence (or perhaps brightfield)
                    # the reference image type (e.g. nuclear dye or brightfield) should be the consisently chosen for all rounds
                    # if the image is a timelapse or round01 then choose the reference channel to be the last channel in the image set , =-1.

                    ref_channel = -2
                    if bool(re.search('time|1(?![0-9])',round_num, re.IGNORECASE)) and round_num!="Round 11": 
                        #print('TODO: make sure this doesnt capture round 11')
                        print("round num is {}".format(round_num))
                        ref_channel=-1
                        print("ref channel is {}".format(ref_channel))

                    # use the parent czi file for metadata
                    # find the channel names for the image file
                    reader = AICSImage(fpath)
                    channels = reader.channel_names
                    
                    # iterate through all scenes in metadata and look for valid scenes (i.e. scenes with image data)
                    # if scene lacks image data, mark it as a scene to toss (it has no image data!)
                    scenes_to_toss=[]
                    for scene in reader.scenes:
                        reader.set_scene(scene)
                        si =reader.current_scene_index
                        try: 
                            dims = reader.dims
                        except:
                            scenes_to_toss.append(si+1)

                    zscenes_to_toss=','.join([str(x) for x in scenes_to_toss])
                    zchannels = ','.join(channels)
                    #the names for these yaml entries are weird (i.e. "iround") because they get organized alphabetically and I want them to appear in a desired order
                    print(f"channels are {zchannels}")
                    detailid={}
                    detailid['round'] = round_num
                    detailid['item'] = 'czi'
                    detailid['zchannels'] = zchannels
                    detailid['path'] = fpath
                    detailid['scenes_to_toss'] = zscenes_to_toss
                    detailid['ref_channel'] = str(channels[ref_channel])
                    config['Data'].append(detailid)
                # yamd['Data'].append(subd)
            config['barcode'] = barcode
            config['scope'] = scope
            
            # output path defies folder where all images get stored after they get processed
            # Should define this now or later?
            config['output_path'] = args.output_yaml_dir

        
        output_dir = os.path.join(args.output_path,'json_configs')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        out_path = os.path.join(output_dir, f"{barcode}_initial.json")
        print(out_path)
        #config_out = json.dumps(config, indent=4, sort_keys=True)

        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)


    