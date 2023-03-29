# -*- coding: utf-8 -*-
import os


# def get_tasklist(db, final_task='geometry'):
#     # Create the list of tasks
#     tasks = list()

#     if final_task == 'deinterlace':
#         tasks = ['deinterlace']
#         if 'rgb' in db['common']['options']['deinterlace_add_tasks']:
#             tasks.append('deinterlace_rgb')
#     elif final_task == 'pre_upscale':
#         tasks = ['deinterlace', 'pre_upscale']

#     elif final_task == 'upscale':
#         tasks = ['deinterlace', 'pre_upscale', 'upscale']
#         if 'geometry' in db['common']['options']['upscale_add_tasks']:
#             try: tasks.remove('pre_upscale')
#             except: pass
#             tasks.append('upscale_rgb_geometry')

#     if final_task == 'sharpen':
#         tasks = ['deinterlace', 'pre_upscale', 'upscale', 'sharpen']
#     elif final_task == 'rgb':
#         tasks = ['deinterlace', 'pre_upscale', 'upscale', 'sharpen', 'rgb']
#     elif final_task in ['all', 'geometry']:
#         tasks = ['deinterlace', 'pre_upscale', 'upscale', 'sharpen', 'rgb', 'geometry']


#     return tasks



# def simplify_tasks(db, frames):
#     # TODO:
#     # - add 'force' switch

#     for f in frames:
#         if 'geometry' in f['tasks'] and os.path.exists(f['filepath']['geometry']):
#             # print("remove RGB curves from tasks")
#             for t in ['deinterlace', 'pre_upscale', 'upscale', 'sharpen', 'rgb']:
#                 try: f['tasks'].remove(t)
#                 except: continue
#             f['tasks'].remove('geometry')

#         if 'deinterlace_rgb' in f['tasks'] and os.path.exists(f['filepath']['deinterlace_rgb']):
#             f['tasks'].remove('deinterlace_rgb')


#         if 'rgb' in f['tasks'] and os.path.exists(f['filepath']['rgb']):
#             # print("remove RGB curves from tasks")
#             for t in ['deinterlace', 'pre_upscale', 'upscale', 'sharpen']:
#                 try: f['tasks'].remove(t)
#                 except: continue
#             f['tasks'].remove('rgb')

#         elif 'sharpen' in f['tasks'] and os.path.exists(f['filepath']['sharpen']):
#             # print("remove sharpen from tasks")
#             for t in ['deinterlace', 'pre_upscale', 'upscale', 'denoise']:
#                 try: f['tasks'].remove(t)
#                 except: continue
#             f['tasks'].remove('sharpen')


#         elif 'upscale' in f['tasks'] and os.path.exists(f['filepath']['upscale']):
#             for t in ['deinterlace', 'pre_upscale', 'upscale']:
#                 try: f['tasks'].remove(t)
#                 except: continue

#         elif 'pre_upscale' in f['tasks'] and os.path.exists(f['filepath']['pre_upscale']):
#             for t in ['deinterlace', 'pre_upscale']:
#                 try: f['tasks'].remove(t)
#                 except: continue

#         elif ('pre_upscale' in f['tasks']
#             and f['filters']['ffmpeg']['pre_upscale'] is None
#             and f['filters']['opencv']['pre_upscale'] is None):
#             for t in ['deinterlace', 'pre_upscale']:
#                 try: f['tasks'].remove(t)
#                 except: continue

#         elif 'deinterlace' in f['tasks'] and os.path.exists(f['filepath']['deinterlace']):
#             try: f['tasks'].remove('deinterlace')
#             except: continue


