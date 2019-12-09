#!/bin/sh

while true;
do
      num="$(git ls-files --others --exclude-standard | wc -l)"
      if [ $num -gt 0 ]
      then
        git ls-files --others --exclude-standard | head -n 100 | xargs -n 1 git add
        git commit -m 'adding partial set of podcasts'
        git push
      else
        break
      fi
done
