import twitch_crawler as tc


if __name__ == '__main__':
    print('Program start')

    top_games_cat = tc.scrape_categories(1)
    top_games = tc.scrape_games(top_games_cat, 1)
    tc.quit_driver()
    print(top_games)

    print('Program complete')


# to rebuild html docs, run this in /docs:
# make html
# open _build/html/index.html in a browser

