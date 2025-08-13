# Suno Metatag Collector v2.0.1

Single-script workflow that captures tokens, keeps them fresh with a background watcher, crawls all Suno workspaces, and exports a neat Excel workbook (plus optional Parquet).

**New in v2.0.1:**
- Excel auto-named `suno_clips_YYYY-MM-DD.xlsx`. If a file with today’s date exists, a numeric suffix is added: `suno_clips_YYYY-MM-DD_1.xlsx`, `…_2.xlsx`, etc.
- Version is logged at the start of each run, along with short notes.
- This README lists the current extracted metadata fields (94), subject to change as Suno evolves.

**Security default:** On successful completion, token files `auth.json` and `auto.json` are deleted automatically.

## Requirements
- **Python 3.9+**
- Install:
  ```bash
  pip install -r requirements.txt
  ```
- Linux clipboard (for auto-watching):
  ```bash
  sudo apt-get install -y xclip   # or: sudo apt-get install -y xsel
  ```

## Quick Start
1. Open https://suno.com/me in your browser.
2. DevTools → Network → filter **Fetch/XHR**.
3. Click “Next page” so the Network list refreshes.
4. Find the `GET` starting with:
   ```
   https://studio-api.prod.suno.com/api/feed/v2?hide_disliked=true&hide_gen_stems=true&hide_studio_clips=true&page=...
   ```
5. Right-click → **Copy** → **Copy as cURL (bash)**.
6. Run:
   ```bash
   python suno_metadata_collector.py
   ```
   Paste when prompted, press Enter on a blank line.

## File naming
- Excel is saved as `suno_clips_YYYY-MM-DD.xlsx`.
- If that already exists, the script appends a suffix: `suno_clips_YYYY-MM-DD_1.xlsx`, then `_2`, etc.
- Parquet (optional) is saved as `suno_clips.parquet` when `--write-parquet` is used and `pyarrow` is installed.

## Extracted metadata (94 fields, will evolve)
As of this writing, the script flattens and exports these fields. Future Suno changes may add/remove fields.

- project_name
- project_id
- allow_comments
- audio_url
- avatar_image_url
- caption
- comment_count
- created_at
- display_name
- display_tags
- download_disabled_reason
- entity_type
- explicit
- flag_count
- handle
- has_hook
- id
- image_large_url
- image_url
- is_contest_clip
- is_handle_updated
- is_liked
- is_public
- is_trashed
- major_model_version
- metadata.artist_clip_id
- metadata.can_publish_with_vocal
- metadata.can_remix
- metadata.concat_history
- metadata.control_sliders.audio_weight
- metadata.control_sliders.style_weight
- metadata.control_sliders.weirdness_constraint
- metadata.cover_clip_id
- metadata.duration
- metadata.edit_session_id
- metadata.edited_clip_id
- metadata.error_message
- metadata.error_type
- metadata.gpt_description_prompt
- metadata.has_stem
- metadata.has_vocal
- metadata.history
- metadata.infill
- metadata.infill_lyrics
- metadata.is_audio_upload_tos_accepted
- metadata.is_loudness_under_threshold
- metadata.is_remix
- metadata.negative_tags
- metadata.persona_id
- metadata.playlist_id
- metadata.priority
- metadata.prompt
- metadata.refund_credits
- metadata.show_remix
- metadata.speed_clip_id
- metadata.stem_from_id
- metadata.stem_task
- metadata.stem_type_group_name
- metadata.stem_type_id
- metadata.stream
- metadata.styles_lyrics_clip_id
- metadata.tags
- metadata.task
- metadata.type
- metadata.upsample_clip_id
- metadata.video_is_stale
- model_name
- persona.id
- persona.image_s3_id
- persona.is_owned
- persona.is_public
- persona.is_trashed
- persona.name
- persona.root_clip_id
- persona.user_display_name
- persona.user_handle
- persona.user_image_url
- play_count
- project.description
- project.id
- project.is_public
- project.is_trashed
- project.name
- reaction.feedback_reason
- reaction.flagged
- reaction.play_count
- reaction.reaction_type
- reaction.skip_count
- reaction.updated_at
- status
- title
- upvote_count
- user_id
- video_url

## CLI options
```text
--out-dir PATH          Output directory (default: suno_api_dump)
--workspace NAME        Filter to specific workspace(s). Repeat for multiple.
--open-excel true|false Auto-open Excel when done (default: true)
--no-watcher            Disable clipboard watcher (manual pasting only)
--write-parquet         Also write suno_clips.parquet (requires pyarrow)
--log-dir PATH          Directory to write logs (default: logs)
```

## Normal messages
- `Waiting for auth.json refresh …` or `[!] 401 Unauthorized. Waiting for new token.`  
  Copy a fresh **Copy as cURL (bash)**. The watcher updates `auth.json` automatically.
- `[!] 429 Too Many Requests.`  
  Normal. The script backs off and retries.
- Progress lines:
  ```
  • page 12    adding 20 new rows   total # of rows 240
  ```

## Outputs
- `auth.json` (deleted automatically on success)
- `suno_api_dump/pages/*.json`
- `suno_api_dump/*_clips.json`
- `suno_clips_YYYY-MM-DD.xlsx` (auto-suffixed if needed)
- `suno_clips.parquet` (optional, with `--write-parquet`)

## Credits
- Code by **tedy02**, 2025  
- Coding assistance by **Chat-GPT**

## Future roadmap
Here are the changes/enhancements I would like to make in the future. If you have the ability to implement any of these for me that would be awesome. I am new to coding, this is my first GitHub project.
- Add CLI overrides to toggle feed filters: disliked, studio clips, generated stems. Today these are hardcoded to `true`. A future flag would allow quick opt-in/out.
- Let users exclude certain metadata/columns at export time.
- Support multiple output formats beyond Excel and Parquet, like HTML or PDF.

## License
MIT
