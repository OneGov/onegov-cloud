from onegov.api import ApiEndpoint
from onegov.ballot import VoteCollection


class VoteApiEndpoint(ApiEndpoint):

    endpoint = 'votes'

    def query(self, session):
        try:
            year = int(self.filter.get('year'))
        except (KeyError, TypeError, ValueError):
            year = None

        collection = VoteCollection(session, page=self.page, year=year)
        collection.batch_size = 50
        return [
            {
                'id': item.id
            }
            for item in collection.batch
        ]

        # application/hal+json

        # {
        #     "_links": {
        #         "self": { "href": "https://api.example.com/player/1234567890/friends" },
        #         "next": { "href": "https://api.example.com/player/1234567890/friends?page=2" }
        #     },
        #     "size": "2",
        #     "_embedded": {
        #         "player": [
        #             {
        #                 "_links": {
        #                     "self": { "href": "https://api.example.com/player/1895638109" },
        #                     "friends": { "href": "https://api.example.com/player/1895638109/friends" }
        #                 },
        #                 "playerId": "1895638109",
        #                 "name": "Sheldon Dong",
        #                 "alternateName": "sdong",
        #                 "image": "https://api.example.com/player/1895638109/avatar.png"
        #             },
        #             {
        #                 "_links": {
        #                     "self": { "href": "https://api.example.com/player/8371023509" },
        #                     "friends": { "href": "https://api.example.com/player/8371023509/friends" }
        #                 },
        #                 "playerId": "8371023509",
        #                 "name": "Martin Liu",
        #                 "alternateName": "mliu",
        #                 "image": "https://api.example.com/player/8371023509/avatar.png"
        #             }
        #         ]
        #     }
        # }
