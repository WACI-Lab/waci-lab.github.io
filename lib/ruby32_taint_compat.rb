# Ruby 3.2+ removed Kernel#tainted?/#taint/#untaint/#trust/#untrust, but the
# Liquid 4.0.3 pulled in by the `github-pages` gem (which pins Jekyll/Liquid
# to match GitHub Pages' production build, and disables the `_plugins`
# directory entirely to mirror that same sandbox) still calls `tainted?` on
# every rendered variable. Without this shim, `jekyll build`/`serve` crashes
# on modern Ruby with:
#   NoMethodError: undefined method 'tainted?' for an instance of String
#
# github-pages forces `plugins_dir` to a random, nonexistent path (see
# github-pages/configuration.rb), so a normal _plugins/*.rb file never
# loads. This file is instead required directly from the Gemfile, which
# Bundler evaluates in-process on every `bundle exec` before Jekyll/Liquid
# are loaded — so the patch is in place before anything can call
# `tainted?`. It has no effect on what actually gets published to GitHub
# Pages (that build runs on GitHub's own, compatible Ruby).
unless Object.method_defined?(:tainted?)
  module Ruby32TaintCompatShim
    def tainted?
      false
    end

    def taint
      self
    end

    def untaint
      self
    end

    def trust
      self
    end

    def untrust
      self
    end
  end

  Object.include(Ruby32TaintCompatShim)
end
