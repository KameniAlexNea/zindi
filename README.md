# zindi-package

## Description

A user-friendly Python client for interacting with the Zindi platform.

## Installation

```bash
pip install -U zindi
```

## Quick start

```python
from zindi.user import Zindian

# interactive mode (prints formatted tables/messages)
user = Zindian(username="your_username")

# or tool/MCP-friendly mode (returns typed models)
# user = Zindian(username="your_username", return_models=True, to_print=False)
```

## Usage

You can also check the [Colab notebook](https://colab.research.google.com/drive/1zzAUWkJ8R5GQzxsdJ5i7XTxaGe2tmUF4?usp=sharing).

```python
# 1) Select challenge
selection = user.select_a_challenge(challenge_id="digicow-farmer-training-adoption-challenge")

# 2) Inspect challenge/rank
current = user.which_challenge
rank = user.my_rank

# 3) Leaderboard and submission board
leaderboard = user.leaderboard(per_page=50)
board = user.submission_board(per_page=50)

# 4) Download dataset and submit file
files = user.download_dataset(destination="./dataset")
submission = user.submit(
	filepaths=["./dataset/SampleSubmission.csv"],
	comments=["initial submission"],
)

# 5) Team actions
team = user.create_team(team_name="New Team")
```

### Typed model outputs (recommended for integrations)

```python
user = Zindian(username="your_username", return_models=True, to_print=False)

selection = user.select_a_challenge(query="DigiCow")
print(selection)             # ChallengeSelectionResult(...)

leaderboard = user.leaderboard(per_page=10)
print(leaderboard)           # LeaderboardResult(rank=..., total_rows=...)

submissions = user.submission_board(per_page=20)
print(submissions)           # SubmissionBoardResult(total_rows=...)

payload = leaderboard.to_dict()   # JSON-serializable dictionary
```

## Contributors

<div align='center'>

| <img src='https://avatars.githubusercontent.com/u/28601730?v=4' width='100' height='100' style='border-radius:50%; margin:.8cm'> <br>Emmanuel KOUPOH                        | <img src='https://avatars.githubusercontent.com/u/45067126?v=4' width='100' height='100' style='border-radius:50%; margin:.8cm'> <br>Cédric MANOUAN                      | <img src='https://avatars.githubusercontent.com/u/28511546?v=4' width='100' height='100' style='border-radius:50%; margin:.8cm'> <br>Muhamed TUO                      | <img src='https://avatars.githubusercontent.com/u/45461704?s=96&v=4' width='100' height='100' style='border-radius:50%; margin:.8cm'> <br>Elie Alex Kameni Ngangue                      |
|--------------------------------------|-------------------------------|----------------------------------------------|----------------------------------------------|
| [eaedk](https://github.com/eaedk) | [dric2018](https://github.com/dric2018) | [NazarioR9](https://github.com/NazarioR9)| [KameniAlexNea](https://github.com/KameniAlexNea) |
| [Emmanuel on linkedin](https://www.linkedin.com/in/esaïe-alain-emmanuel-dina-koupoh-7b974a17a) | [Cedric on linkedin](https://www.linkedin.com/in/cédric-pascal-emmanuel-manouan-ba9ba1181) | [Muhamed on linkedin](https://www.linkedin.com/in/muhamed-tuo-b1b3a0162) | [Alex on linkedin](https://www.linkedin.com/in/elie-alex-kameni-ngangue) |
|[@eaedk😂](https://zindi.africa/users/eaedk) | [@Zeus😆](https://zindi.africa/users/I_am_Zeus_AI) |   [@Nazario😁](https://zindi.africa/users/Muhamed_Tuo)   | [@alexneakameni🤗](https://zindi.africa/users/Kamenialexnea) |

<br>


Don’t forget to visit [Zindi Platform](https://www.zindi.africa)<br>
<img src='https://yt3.ggpht.com/NLdtJ6iB3VS1-4hxjNf5ODgSYxGx4Dvpi25J4KBc3rT5HlSSyqqEW4zvKi8KJtDlxQXxdb5FFao=s68-c-k-c0x00ffffff-no-rj' width='90%' height='200' style='border-radius:5; margin:.8cm'>
