# TODO
- effects: verify when replacing shots (asuivre)
- (?) custom filter depending on shot
- (?) g_fin : fadeout is not done
- (?) process single frame does not work anymore: repair and re-enable ?
- stabilize: modify tools
- replace:
    * when in memory mode, do not flush images but replace images (copy)
    * Circular dependency is not verified
- rgb/geometry: error when processing shot
- use file hash for rgb step
- FFmpeg filter:
    * (?) use concatenate for all cases -> save images before
    * use ffv1 for FFmpeg filter except if images already exists.
- Do not save pre_upscaled images if not specified in filters


- video editor:
    * curves: find shot from frame no and do not verify if it is the 1st frame. when saving, use middle of shot?
