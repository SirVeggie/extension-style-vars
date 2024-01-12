# Style variables SD extension

Use styles or parts of them as variables inside the prompt.

## Motivation

This extension offers a more flexible use of styles. By using them as variables you can easily control the position of the styles more freely.

You can also use styles inside prompt editing for example:  
`[$style1|$style2]`  
which is not possible with the native use of styles.

## Syntax

`$style` will be replaced with the style text  
`$(a style)` parentheses can be used if the style name has spaces  
`$1style` or `$1(style)` can be used to select the first part of a style. Parts are separated by `{prompt}`  
You can have any number of parts by having multiple `{prompt}` in the style and using `$2`, `$3`, etc...  
`$style` will be replaced by the negative part of the style when used in the negative prompt

## Extra features (new)

All extra features can be toggled individually in settings, syntax based features are off by default to prevent conflict with other extensions.

### Original prompt save and load
Saves the original prompt into parameters to preserve style variables, random and hires prompting syntax when loading prompt data.

### Prompt randomization
Basic prompt randomization `{one|two|three}` chooses one of the choices randomly (basic version of dynamic prompts)

Unlike dynamic prompts, this can be nested with itself or **even with other syntax** like prompt editing `[one|two]`

### Hires prompting
Modify hires prompt directly from main prompt with `{lowres prompt:hires prompt}`

Hires prompting can also be nested with most prompting syntax.

This allows incrementally changing prompt for hires without using the hires prompt box (no need to copy paste entire prompt just to change something in hires)

I recommend adding `Hires prompt` and `Hires negative prompt` to disregarded fields from pasted info text in settings -> user interface -> infotext.

### Remove line breaks and extra whitespace
Removes unnecessary whitespace like duplicate spaces, and replaces line breaks with commas. (Does not create duplicate commas if there is already a comma before or after a line break)

## Examples

<details>
<summary>Styles</summary>

cinematic  
pos: ```cinematic perspective, letterboxing```  
neg: ```colorful, cute```

artistic  
pos: ```van gogh, {prompt}, abstract artstyle, {prompt}, landscape```  
neg: ```blurry, ugly```
</details>

### Basic use
`oil painting, $cinematic, man standing in rain`  
->  
`oil painting, cinematic perspective, letterboxing, man standing in rain`

### {prompt} parts are removed automatically
`playground, $artistic`  
->  
`playground, van gogh, abstract artstyle, landscape`

### Mixing parts and using negative
pos: `$3artistic, man, $1(artistic)`  
neg: `3D, $cinematic`  
->  
pos: `landscape, man, van gogh`  
neg: `3D, colorful, cute`

### Create more 3D-like anime images
Create a 3d base image, then use flat anime styling in hires

pos: `cute girl, {realistic, 3d:anime style, flat digital art}`  
neg: `worst quality, abstract, {:3d, realistic}`  
->  
pos: `cute girl, realistic, 3d`  
neg: `worst quality, abstract, `  
hires pos: `cute girl, anime style, flat digital art`  
hires neg: `worst quality, abstract, 3d, realistic`