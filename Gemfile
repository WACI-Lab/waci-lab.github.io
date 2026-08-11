source "https://rubygems.org"

# Must run before `github-pages`/Jekyll/Liquid load below — see the file for why.
require_relative "lib/ruby32_taint_compat"

gem "github-pages", group: :jekyll_plugins

group :jekyll_plugins do
  gem "jekyll-feed"
  gem "jekyll-sitemap"
end
# Ruby 3.4+ no longer bundles these by default, but the older Jekyll
# pulled in by the github-pages gem still expects them at require-time.
gem "csv"
gem "webrick"
gem "logger"
gem "base64"
gem "bigdecimal"

# Windows and JRuby does not include zoneinfo files
install_if -> { RUBY_PLATFORM =~ %r!mingw|mswin|java! } do
  gem "tzinfo", ">= 1", "< 3"
  gem "tzinfo-data"
end
