import logging
import re
import random
from copy import deepcopy

# import gradio as gr
from gradio.components import Component
from modules import shared, script_callbacks, scripts
from modules.processing import StableDiffusionProcessing, StableDiffusionProcessingTxt2Img


# variables
extn_name = "Style Variables"
extn_id = "style_vars"
extn_enabled = extn_id + "_enabled"
extn_random = extn_id + "_random"
extn_hires = extn_id + "_hires"
extn_linebreaks = extn_id + "_linebreaks"
extn_info = extn_id + "_info"

TS_PROMPT = "sv_prompt"
TS_NEG = "sv_negative"

logger = logging.getLogger(extn_id)
logger.setLevel(logging.INFO)

var_char = "$"


# regexes
re_prompt = re.compile(r",? *\{prompt\} *,? *", re.I)
re_group = re.compile(r"^_\d+_$")


# helper functions
def check_enabled():
    return getattr(shared.opts, extn_enabled) is True
def check_feature(name: str):
    return check_enabled() and getattr(shared.opts, name) is True

def build_var(name: str):
    if " " in name:
        return f"{var_char}({name})"
    return f"{var_char}{name}"

def is_opening(text, i):
    list = ['{', '(', '[', '<']
    return text[i] in list and (i == 0 or text[i-1] != '\\')
def is_closing(text, i):
    list = ['}', ')', ']', '>']
    return text[i] in list and (i == 0 or text[i-1] != '\\')
def decode(text: str, hires: bool, neg: bool, seed: int):
    depth = 0
    start = -1
    end = -1
    mode = "random"
    splits = []
    rand = random.Random(seed + (1 if neg else 0))
    
    if len(text) == 0:
        return text
    
    i = -1
    while i + 1 < len(text):
        i += 1
        
        if is_opening(text, i):
            if depth == 0 and text[i] != '{':
                continue
            if depth == 0:
                start = i
            depth += 1
        elif is_closing(text, i):
            if depth > 0:
                depth -= 1
            if depth == 0 and text[i] == '}' and start != -1:
                end = i
        elif text[i] == '|' and depth == 1:
            splits.append(i)
        elif text[i] == ':' and depth == 1:
            splits.append(i)
            mode = "hr"
        
        if end != -1:
            if mode == "hr" and len(splits) > 1:
                logger.error("Warning: multiple splits in hr mode")
                return text
            
            if mode == "hr" and check_feature(extn_hires):
                part1 = text[start+1:splits[0]]
                part2 = text[splits[0]+1:end]
                part = part2 if hires else part1
                text = text[:start] + part + text[end+1:]
                
            elif mode == "random" and check_feature(extn_random):
                parts = []
                if len(splits) == 0:
                    parts.append(text[start+1:end])
                else:
                    for k in range(len(splits)):
                        if k == 0:
                            parts.append(text[start+1:splits[k]])
                        else:
                            parts.append(text[splits[k-1]+1:splits[k]])
                    parts.append(text[splits[-1]+1:end])
                
                custom_seed = parts.pop(0) if re_group.match(parts[0]) else None
                if custom_seed:
                    part = random.Random(seed + custom_seed).choice(parts)
                else:
                    part = rand.choice(parts)
                text = text[:start] + part + text[end+1:]
            
            else:
                start += 1
            
            i = start - 1
            start = -1
            end = -1
            splits = []
            mode = "random"
    
    return text

# register callbacks
def on_ui_settings():
    section = (extn_id, extn_name)
    shared.opts.add_option(extn_enabled, shared.OptionInfo(True, "Enable extension", section=section))
    shared.opts.add_option(extn_random, shared.OptionInfo(False, "Enable randomization syntax: {one|two|three}", section=section))
    shared.opts.add_option(extn_hires, shared.OptionInfo(False, "Enable hires prompt syntax: {normal prompt:hires prompt}", section=section))
    shared.opts.add_option(extn_linebreaks, shared.OptionInfo(True, "Remove linebreaks", section=section))
    shared.opts.add_option(extn_info, shared.OptionInfo(True, "Save and load original prompt from generation info", section=section))

def on_infotext_pasted(prompt: str, params: dict[str, str]):
    if not check_feature(extn_info):
        return
    if TS_PROMPT in params:
        params["Prompt"] = params.get(TS_PROMPT, params["Prompt"])
    if TS_NEG in params:
        params["Negative prompt"] = params.get(TS_NEG, params["Negative prompt"])

script_callbacks.on_ui_settings(on_ui_settings)
script_callbacks.on_infotext_pasted(on_infotext_pasted)

# class
class StyleVars(scripts.Script):
    is_txt2img: bool = False

    infotext_fields: list[tuple[Component, str]] = []

    def title(self):
        return extn_name

    def show(self, is_img2img: bool):
        return scripts.AlwaysVisible

    # def ui(self, is_img2img: bool) -> list[Component]:
    #     with gr.Accordion(label=extn_name, open=False):
    #         with gr.Row(elem_id=f"{extn_id}_row"):
    #             enabled = gr.Checkbox(
    #                 label="Enabled",
    #                 value=True,
    #                 description="Enable prompt processing",
    #                 elem_id=f"{extn_id}_enabled",
    #                 scale=1,
    #             )
    #     return [enabled]

    def process(
        self,
        p: StableDiffusionProcessing,
        *args,
    ):
        if not check_enabled():
            return
        style_names: list[str] = shared.prompt_styles.styles.keys()
        style_names = sorted(style_names, key=len, reverse=True)

        def rewrite_prompt(prompt: str, neg: bool, hires: bool, seed: int):
            if check_feature(extn_linebreaks):
                prompt = re.sub(r"[\s,]*[\n\r]+[\s,]*", ", ", prompt)
                prompt = re.sub(r"\s+", " ", prompt)
            
            depth = 0
            previous_prompt = prompt
            while depth < 5:
                prompt = decode(prompt, hires, neg, seed)
                
                for name in style_names:
                    if name not in prompt:
                        continue
                    mode = 2 if neg else 1
                    
                    # normal vars
                    text = shared.prompt_styles.styles[name][mode]
                    parts = re_prompt.split(text)
                    text = ", ".join(parts)
                    if " " not in name:
                        prompt = prompt.replace(f"{var_char}{name}", text)
                    prompt = prompt.replace(f"{var_char}({name})", text)
                    
                    # split vars
                    for i, part in enumerate(parts):
                        if " " not in name:
                            prompt = prompt.replace(f"{var_char}{i+1}{name}", part)
                        prompt = prompt.replace(f"{var_char}{i+1}({name})", part)
                
                if prompt == previous_prompt:
                    break
                previous_prompt = prompt
                depth += 1
            
            # return the rewritten prompt
            return prompt

        # check if we're doing t2i with HR
        is_t2i = isinstance(p, StableDiffusionProcessingTxt2Img)
        hr_enabled = p.enable_hr if is_t2i else False
        
        if check_feature(extn_info):
            orig_pos_prompt = deepcopy(p.all_prompts[0])
            orig_neg_prompt = deepcopy(p.all_negative_prompts[0])
        else:
            orig_pos_prompt = ""
            orig_neg_prompt = ""

        batch_size = p.batch_size
        for b_idx in range(p.n_iter):
            for s_offs in range(batch_size):
                s_idx = b_idx * batch_size + s_offs  # offset of the prompt in all_prompts

                s_prompt = rewrite_prompt(p.all_prompts[s_idx], False, False, p.all_seeds[s_idx])
                p.all_prompts[s_idx] = s_prompt
                logger.debug(f"[B{b_idx:02d}][I{s_offs:02d}] prompt: {s_prompt}")

                s_neg_prompt = rewrite_prompt(p.all_negative_prompts[s_idx], True, False, p.all_seeds[s_idx])
                p.all_negative_prompts[s_idx] = s_neg_prompt
                logger.debug(f"[B{b_idx:02d}][I{s_offs:02d}] neg prompt: {s_neg_prompt}")

                if is_t2i and hr_enabled:
                    s_hr_prompt = rewrite_prompt(p.all_hr_prompts[s_idx], False, True, p.all_seeds[s_idx])
                    p.all_hr_prompts[s_idx] = s_hr_prompt
                    if s_hr_prompt != s_prompt:
                        logger.debug(f"[B{b_idx:02d}][I{s_offs:02d}] HR prompt: {s_hr_prompt}")

                    s_hr_neg_prompt = rewrite_prompt(p.all_hr_negative_prompts[s_idx], True, True, p.all_seeds[s_idx])
                    p.all_hr_negative_prompts[s_idx] = s_hr_neg_prompt
                    if s_hr_neg_prompt != s_neg_prompt:
                        logger.debug(f"[B{b_idx:02d}][I{s_offs:02d}] HR neg prompt: {s_hr_neg_prompt}")

        if check_feature(extn_info):
            p.extra_generation_params.setdefault(TS_PROMPT, orig_pos_prompt)
            p.extra_generation_params.setdefault(TS_NEG, orig_neg_prompt)