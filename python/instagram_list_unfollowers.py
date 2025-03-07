
# pip3 install instaloader
import instaloader
from dotenv import load_dotenv
from os import getenv


def login_instagram(username, password):
    """
    Function to log into Instagram using the instaloader library.

    Parameters:
    username (str): The Instagram account username
    password (str): The Instagram account password

    Returns:
    L (instaloader.Instaloader): The instaloader object for API calls
    profile (instaloader.Profile): The user's Instagram profile
    """
    L = instaloader.Instaloader()
    L.interactive_login(username)
    profile = instaloader.Profile.from_username(L.context, username)
    return L, profile


def get_non_followers(profile):
    """
    Function to get a list of non-followers (people you follow who don't follow you back).

    Parameters:
    profile (instaloader.Profile): The user's Instagram profile

    Returns:
    non_followers (list of str): The list of non-followers' usernames
    """
    followers = set(profile.get_followers())
    followees = set(profile.get_followees())
    non_followers = followees - followers
    return [user.username for user in non_followers]


def main():
    """
    Main function to login into Instagram and print the list of non-followers.
    """
    load_dotenv()
    username = getenv("INSTAGRAM_USERNAME")
    password = getenv("INSTAGRAM_PASSWORD")

    L, profile = login_instagram(username, password)
    non_followers = get_non_followers(profile)

    print("Non-followers:")
    for user in non_followers:
        print(user)


if __name__ == "__main__":
    main()
