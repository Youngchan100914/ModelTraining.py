import json
from modules.print import bcolors
brawler_stats_dict = json.load(open("brawler_stats.json"))

class Constants:
    brawler_name = "SAMPLE_NAME"

    speed = 2.4 # units: (tiles per second)
    attack_range = 9.33 # units: (tiles)
    heightScaleFactor = 0.158
    sharpCorner = True
    centerOrder = True

    window_name = "Bluestacks App Player"
    # Make this False if detection_test is outputting a blank screen, otherwise True.
    focused_window = False

    #! Change this to True if you have Nvidia graphics card and CUDA installed
    nvidia_gpu = False

    DEBUG = False

    classes = ["Player","Bush","Enemy","Cubebox"]
    threshold = [0.37,0.47,0.57,0.65]

    try:
        brawler_stats = brawler_stats_dict[brawler_name.lower().strip()]
        display_str = f"Using {brawler_name.upper()}'s stats if your selected brawler is not {brawler_name.upper()},\nplease manually modify at constants.py."
        standard_hsf = 0.15
        if len(brawler_stats) == 2:
            brawler_stats.append(standard_hsf)
        elif len(brawler_stats) > 3:
            display_str = f"{brawler_name} in brawler_stats.json has more then 3 element, using stats at constants.py"
            brawler_stats = 3*[None]
    except KeyError:
        brawler_stats = 3*[None]
        display_str = f"{brawler_name.upper()}'s stats is not found in the JSON. \nUsing speed, attack_range and heightScaleFactor in constant.py.\nPlease manually modify at constants.py if you have not."
    speed = brawler_stats[0] or speed # units: (tiles per second)
    attack_range = brawler_stats[1] or attack_range # units: (tiles per second)
    heightScaleFactor = brawler_stats[2] or heightScaleFactor
    print(bcolors.OKBLUE + f"speed: {speed} tiles/second \nattack_range: {attack_range} tiles\nHeightScaleFactor: {heightScaleFactor}" + bcolors.ENDC)

    # interface
    if nvidia_gpu is None:
        # load TensorRT interface
        model_file_path = "yolov8_model/yolov8.engine"
        half = False
        imgsz = 640
    elif nvidia_gpu:
        # load pytorch interface
        model_file_path = "yolov8_model/yolov8.pt"
        half = False
        imgsz = (384,640)
    else:
        # load openvino interface
        model_file_path = "yolov8_model/yolov8_openvino_model"
        half = True
        imgsz = (384,640)
    #bot constant
    movement_key = "middle"
    midpoint_offset = 12
    
    float_int_dict = {
        "speed":speed,
        "attack_range":attack_range,
        "heightScaleFactor": heightScaleFactor
    }

    bool_dict = {
        "sharpCorner": sharpCorner,
        "centerOrder": centerOrder,
    }

    for key in float_int_dict:
        assert type(float_int_dict[key]) == float or type(float_int_dict[key]) == int, f"{key.upper()} should be a integer or a float"

    for key in bool_dict:
        assert type(bool_dict[key]) == bool,f"{key.upper()} should be True or False"

if __name__ == "__main__":
    pass