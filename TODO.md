# TODO
- hash: deshake is using 3 lines in log...
- effects: verify when replacing shots (asuivre)
- (?) custom filter depending on shot
- (?) g_fin : fadeout is not done
- (?) process single frame does not work anymore: repair and re-enable ?
- stabilize: modify tools
- tools: filters have been modified->modify combobox
- replace:
    * when in memory mode, do not flush images but replace images (copy)
    * Circular dependency is not verified
- rgb/geometry: error when processing shot
- ffmpeg filter: use concatenate for all cases -> save images before
- combine images at the end of each shot
- use file hash for rgb step
- create a new step 'pre_replace' for frame replacement
- video editor: disable frame replacement widget if step is not 'pre_replace'