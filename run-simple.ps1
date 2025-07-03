python src\video2pose.py `
    .\data\Videos\OAW01-bottom.mp4 `
    --output .\outputs\openpose-toronto-01 `
    --confidence-threshold 0.3 `
    --net-resolution 656x368 `
    --model-pose COCO `
    --overlay-video ".\outputs\overlay.mp4" `
    --toronto-gait-format `
    --extract-comprehensive-frames `
    --verbose