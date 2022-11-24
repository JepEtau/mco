# -*- coding: utf-8 -*-
import os


def get_tasklist(db, final_task='geometry'):
    # Create the list of tasks
    tasks = list()

    if final_task == 'deinterlace':
        tasks = ['deinterlace']
        if 'rgb' in db['common']['options']['deinterlace_add_tasks']:
            tasks.append('deinterlace_rgb')
    elif final_task == 'pre_upscale':
        tasks = ['deinterlace', 'pre_upscale']

    elif final_task == 'upscale':
        tasks = ['deinterlace', 'pre_upscale', 'upscale']
        if 'geometry' in db['common']['options']['upscale_add_tasks']:
            try: tasks.remove('pre_upscale')
            except: pass
            tasks.append('upscale_rgb_geometry')

    elif final_task == 'denoise':
        tasks = ['deinterlace', 'pre_upscale', 'upscale', 'denoise']
    elif final_task == 'bgd':
        tasks = ['deinterlace', 'pre_upscale', 'upscale', 'denoise', 'bgd']
    elif final_task == 'stitching':
        tasks = ['deinterlace', 'pre_upscale', 'upscale', 'denoise', 'bgd', 'stitching']
    elif final_task == 'sharpen':
        tasks = ['deinterlace', 'pre_upscale', 'upscale', 'denoise', 'bgd', 'stitching', 'sharpen']
    elif final_task == 'rgb':
        tasks = ['deinterlace', 'pre_upscale', 'upscale', 'denoise', 'bgd', 'stitching', 'sharpen', 'rgb']
    elif final_task in ['all', 'geometry']:
        tasks = ['deinterlace', 'pre_upscale', 'upscale', 'denoise', 'bgd', 'stitching', 'sharpen', 'rgb', 'geometry']


    # Discard tasks which are defined in the common.ini file
    if 'stitching' in db['common']['options']['discard_tasks']:
        # Discard tasks used for stitching
        try: tasks.remove('bgd')
        except: pass
        try: tasks.remove('stitching')
        except: pass

    return tasks



def simplify_tasks(db, frames):
    # TODO:
    # - add 'force' switch

    for k, layer in frames.items():
        i = 0
        for f in layer:

            if 'geometry' in f['tasks'] and os.path.exists(f['filepath']['geometry']):
                # print("remove RGB curves from tasks")
                for t in ['deinterlace', 'pre_upscale', 'upscale', 'denoise', 'bgd', 'stitching', 'sharpen', 'rgb']:
                    del f['filepath'][t]
                    try: f['tasks'].remove(t)
                    except: pass
                f['tasks'].remove('geometry')
                try: frames['bgd'][i]['tasks'].clear()
                except: pass

            if 'rgb' in f['tasks'] and os.path.exists(f['filepath']['rgb']):
                # print("remove RGB curves from tasks")
                for t in ['deinterlace', 'pre_upscale', 'upscale', 'denoise', 'bgd', 'stitching', 'sharpen']:
                    del f['filepath'][t]
                    try: f['tasks'].remove(t)
                    except: pass
                f['tasks'].remove('rgb')
                try: frames['bgd'][i]['tasks'].clear()
                except: pass

            elif 'sharpen' in f['tasks'] and os.path.exists(f['filepath']['sharpen']):
                # print("remove sharpen from tasks")
                for t in ['deinterlace', 'pre_upscale', 'upscale', 'denoise', 'bgd', 'stitching']:
                    del f['filepath'][t]
                    try: f['tasks'].remove(t)
                    except: pass
                f['tasks'].remove('sharpen')
                try: frames['bgd'][i]['tasks'].clear()
                except: pass

            elif 'stitching' in f['tasks'] and os.path.exists(f['filepath']['stitching']):
                for t in ['deinterlace', 'pre_upscale', 'upscale', 'denoise', 'bgd', 'stitching']:
                    try: f['tasks'].remove(t)
                    except: pass
                if k == 'fgd' and 'bgd' in frames.keys():
                    frames['bgd'][i]['tasks'].clear()

            elif 'bgd' in f['tasks'] and os.path.exists(f['filepath']['bgd']):
                for t in ['deinterlace', 'pre_upscale', 'upscale', 'denoise', 'bgd']:
                    try: f['tasks'].remove(t)
                    except: pass

            elif 'denoise' in f['tasks'] and os.path.exists(f['filepath']['denoise']):
                for t in ['deinterlace', 'pre_upscale', 'upscale', 'denoise']:
                    try: f['tasks'].remove(t)
                    except: pass

            elif 'upscale' in f['tasks'] and os.path.exists(f['filepath']['upscale']):
                for t in ['deinterlace', 'pre_upscale', 'upscale']:
                    try: f['tasks'].remove(t)
                    except: pass

            elif 'pre_upscale' in f['tasks'] and os.path.exists(f['filepath']['pre_upscale']):
                for t in ['deinterlace', 'pre_upscale']:
                    try: f['tasks'].remove(t)
                    except: pass

            elif 'deinterlace' in f['tasks'] and os.path.exists(f['filepath']['deinterlace']):
                try: f['tasks'].remove('deinterlace')
                except: pass

            elif 'deinterlace_rgb' in f['tasks'] and os.path.exists(f['filepath']['deinterlace_rgb']):
                try: f['tasks'].remove('deinterlace_rgb')
                except: pass

            i += 1


