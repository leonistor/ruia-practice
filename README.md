# learning ruia scraper

## jq/fx alternative

https://kellyjonbrazil.github.io/jello/

## commands output to json, yeah!

https://github.com/kellyjonbrazil/jc

## process jsonlines

`cat output/hacker_news.jsonl | jq -s '.' | fx`

## cat specific line

`sed -n 91p output/quotes.jsonl`
