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
<br>

`oil painting, $cinematic, man standing in rain`  
result:  
`oil painting, cinematic perspective, letterboxing, man standing in rain`

pos: `$1artistic, man, $3(artistic)`  
neg: `$cinematic`  
result:  
pos: `van gogh, man, landscape`  
neg: `colorful, cute`