from tfmkt.spiders.common import BaseSpider
from scrapy.shell import inspect_response # required for debugging
import re

from tfmkt.utils import safe_strip

class GamesSpider(BaseSpider):
  name = 'games'

  def parse(self, response, parent):
    """Parse leagues page. From this page follow to the games and fixutres page.

    @url https://www.transfermarkt.co.uk/premier-league/startseite/wettbewerb/GB1
    @returns requests 1 1
    @cb_kwargs {"parent": "dummy"}
    @scrapes type href parent
    """

    footer_links = response.css('div.footer-links')
    for footer_link in footer_links:
      text = footer_link.xpath('a//text()').get()
      if text == "All fixtures & results":
        next_url = footer_link.xpath('a/@href').get()

        cb_kwargs = {
            'base' : {
              'parent': parent
            }
          }

        return response.follow(next_url, self.extract_game_urls, cb_kwargs=cb_kwargs)

  def extract_game_urls(self, response, base):
    """Parse games and fixutres page. From this page follow to each game page.

    @url https://www.transfermarkt.co.uk/premier-league/gesamtspielplan/wettbewerb/GB1/saison_id/2020
    @returns requests 330 390
    @cb_kwargs {"base": {"href": "some_href", "type": "league", "parent": {}}}
    @scrapes type href parent game_id 
    """

    game_links = response.css('a.ergebnis-link')
    for game_link in game_links:
      href = game_link.xpath('@href').get()

      cb_kwargs = {
        'base': {
          'parent': base['parent'],
          'href': href
        }
      }

      yield response.follow(href, self.parse_game, cb_kwargs=cb_kwargs)

  def parse_game(self, response, base):
    """Parse games and fixutres page. From this page follow to each game page.

    @url https://www.transfermarkt.co.uk/caykur-rizespor_fenerbahce-sk/index/spielbericht/3426662
    @returns items 1 1
    @cb_kwargs {"base": {"href": "some_href/3", "type": "league", "parent": {}}}
    @scrapes type href parent game_id result matchday date time stadium attendance
    """

    # uncommenting the two lines below will open a scrapy shell with the context of this request
    # when you run the crawler. this is useful for developing new extractors

    # inspect_response(response, self)
    # exit(1)

    game_id = int(base['href'].split('/')[-1])

    game_box = response.css('div.box-content')

    # extract home and away "boxes" attributes
    home_club_box = game_box.css('div.sb-heim')
    away_club_box = game_box.css('div.sb-gast')

    home_club_href = home_club_box.css('a::attr(href)').get()
    away_club_href = away_club_box.css('a::attr(href)').get()

    home_club_position = home_club_box[0].xpath('p/text()').get()
    away_club_position = away_club_box[0].xpath('p/text()').get()

    # extract date and time "box" attributes
    datetime_box = game_box.css('p.sb-datum')
    date_elements = datetime_box.xpath('node()')

    matchday = date_elements[1].xpath('text()').get()
    date = safe_strip(date_elements[3].xpath('text()').get())
    time = safe_strip(date_elements[4].get().strip())[-7:]

    # extract venue "box" attributes
    venue_box = game_box.css('p.sb-zusatzinfos')

    stadium = safe_strip(venue_box.xpath('node()')[1].xpath('a/text()').get())
    attendance = safe_strip(venue_box.xpath('node()')[1].xpath('strong/text()').get())

    # extract results "box" attributes
    result_box = game_box.css('div.ergebnis-wrap')

    result = safe_strip(result_box.css('div.sb-endstand::text').get())

    item = {
      **base,
      'type': 'game',
      'game_id': game_id,
      'home_club': {
        'type': 'club',
        'href': home_club_href
      },
      'home_club_position': home_club_position,
      'away_club': {
        'type': 'club',
        'href': away_club_href
      },
      'away_club_position': away_club_position,
      'result': result,
      'matchday': matchday,
      'date': date,
      'time': time,
      'stadium': stadium,
      'attendance': attendance
    }
    
    yield item
 