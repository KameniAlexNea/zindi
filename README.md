# zindi-package

## Description

A user-friendly ZINDI package which allow Zindians to achieve all available tasks on ZINDI Platform using this package.

## Installation

Copy and Paste the instruction below in a Terminal or Jupyter Notebook.

```bash
pip install -U zindi
```

## Usage

You can check the [colab notebook here](https://colab.research.google.com/drive/1zzAUWkJ8R5GQzxsdJ5i7XTxaGe2tmUF4?usp=sharing)

```python
# create a user object
from zindi.user import Zindian

my_username = "I_am_Zeus_AI"
user = Zindian(username = my_username)

#desired output
[ 🟢 ] 👋🏾👋🏾 Welcome I_am_Zeus_AI 👋🏾👋🏾


user.select_a_challenge()                               # Select a Zindi challenge

user.which_challenge                                    # Get information about the selected challenge

user.leaderboard()                              # Show the Leaderboard of the selected challenge

user.my_rank                                    # Get the user's leaderboard rank

user.remaining_subimissions                         # Get information about how many submission you can still push now to Zindi

user.submission_board()                         # Show the user's Submission-board of the selected challenge

user.download_dataset(destination="t./dataset") # Download the dataset of the selected challenge

user.submit(filepaths=['./dataset/SampleSubmission.csv'], comments=['initial submission']) # Push a submission to Zindi : the SampleSubmission file

user.remaining_subimissions                             # Get information about how many submission you can still push now to Zindi

user.submission_board()                             # Show the Submission-board of the selected challenge

user.create_team(team_name="New Team")             # Create a team for the selected challenge

```

# Contributers

<div align='center'>

| <img src='https://avatars.githubusercontent.com/u/28601730?v=4' width='100' height='100' style='border-radius:50%; margin:.8cm'> <br>Emmanuel KOUPOH                        | <img src='https://avatars.githubusercontent.com/u/45067126?v=4' width='100' height='100' style='border-radius:50%; margin:.8cm'> <br>Cédric MANOUAN                      | <img src='https://avatars.githubusercontent.com/u/28511546?v=4' width='100' height='100' style='border-radius:50%; margin:.8cm'> <br>Muhamed TUO                      | <img src='https://avatars.githubusercontent.com/u/45461704?s=96&v=4' width='100' height='100' style='border-radius:50%; margin:.8cm'> <br>Elie Alex Kameni Ngangue                      |
|--------------------------------------|-------------------------------|----------------------------------------------|----------------------------------------------|
| [eaedk](https://github.com/eaedk) | [dric2018](https://github.com/dric2018) | [NazarioR9](https://github.com/NazarioR9)| [KameniAlexNea](https://github.com/KameniAlexNea) |
| [Emmanuel on linkedin](https://www.linkedin.com/in/esaïe-alain-emmanuel-dina-koupoh-7b974a17a) | [Cedric on linkedin](https://www.linkedin.com/in/cédric-pascal-emmanuel-manouan-ba9ba1181) | [Muhamed on linkedin](https://www.linkedin.com/in/muhamed-tuo-b1b3a0162) | [Alex on linkedin](https://www.linkedin.com/in/elie-alex-kameni-ngangue) |
|[@eaedk😂](https://zindi.africa/users/eaedk) | [@Zeus😆](https://zindi.africa/users/I_am_Zeus_AI) |   [@Nazario😁](https://zindi.africa/users/Muhamed_Tuo)   | [@alexneakameni🤗](https://zindi.africa/users/Kamenialexnea) |

<br>


Dont forget to visite [ZINDI Plateform](www.zindi.africa)<br>
<img src='https://yt3.ggpht.com/NLdtJ6iB3VS1-4hxjNf5ODgSYxGx4Dvpi25J4KBc3rT5HlSSyqqEW4zvKi8KJtDlxQXxdb5FFao=s68-c-k-c0x00ffffff-no-rj' width='90%' height='200' style='border-radius:5; margin:.8cm'>
