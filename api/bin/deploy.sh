#!/bin/bash
# develop branchをデフォルトで開発したいので
set -e

ORIGIN_URL=`git config --get remote.origin.url`

echo "Started deploying"

if [ `git branch | grep gh-pages` ]
then
  git branch -D gh-pages
fi
git checkout -b gh-pages

find . -maxdepth 1 ! -name 'docs' ! -name '.git'  -exec rm -rf {} \;
mv docs/* .
rm -R docs/

git config user.name "$USER_NAME"
git config user.email "$USER_EMAIL"

git add -fA
git commit --allow-empty -m "$(git log -1 --pretty=%B) [ci skip]"
git push -f $ORIGIN_URL gh-pages

echo "Successfully"

exit 0
