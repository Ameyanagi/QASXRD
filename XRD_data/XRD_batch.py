for i in range (1000):
    #sample 1
    sample_stage1.x.move(22.1)
    sample_stage1.y.move(6.811)
    #dark_frame_preprocessor(_count_qas([pe1], shutter_fs, sample_name, frame_count, subframe_time, subframe_count, delay)
    # fram_count: number of repetitions, subframe_time: expose time, subframe count: number of frames to average
    RE(dark_frame_preprocessor(_count_qas([pe1], shutter_fs, "1-SC75-0", 1, 5, 1, 0)))
    #sample 2
    sample_stage1.x.move(-9.6)
    sample_stage1.y.move(6.911)
    RE(dark_frame_preprocessor(_count_qas([pe1], shutter_fs, "2-SC622-0", 1, 5, 1, 0)))
    #sample 3
    sample_stage1.x.move(-41.1)
    sample_stage1.y.move(7.011)
    RE(dark_frame_preprocessor(_count_qas([pe1], shutter_fs, "3-NMCA-0", 1, 5, 1, 60)))
    #db._catalog._entries.cache_clear()
    

