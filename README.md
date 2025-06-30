# suno_metadata_collector
A set of python scripts to collect all of the Suno song clip's metadata and display it as an Excel file.

Don't worry, most of the heavy lifting is handled by the Python scripts, with much of the process fully automated. However, a few manual steps are still required during metadata collection from Suno.


# INSTRUCTIONS FOR USE

1. Go to **suno.com/create** in your web browser.
2. Open **DevTools**, trigger any **POST** request, and select **Copy as cURL (bash)**.
3. Open a terminal window and run: **python refresh_and_collect.py**
4. Watch for the message **"Unauthorized. Refresh token!"** in the terminal.
5. Each time you see that message, repeat step 2.
6. When the crawler completes, it will display its status and let you know if the **suno_clips.xlsx** Excel file was created/updated successfully.

*Everything else is automated for you!*


# FUTURE IMPROVEMENTS

Feel free to improve or collaborate with me on this script. I'm not a coder, so I'm sure there is a more streamlined way to do this. Combining or automating some steps (especially **step 2**) would be a huge win. If you can simplify the process, particularly by automating the cURL capture, **please reach out**.


# DISCLAIMER

This has only been tested in a **Windows 11** environment.
