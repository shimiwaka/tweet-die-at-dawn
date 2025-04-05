#!/usr/bin/env ruby

require 'json'

def delete_tweet(tweet_id)
  command_file = File.join(File.dirname(__FILE__), 'delete_tweet_command.dat')
  command = File.read(command_file)
  command = command.gsub('TWEET_ID', tweet_id)
  system(command)
end

if ARGV.empty?
  puts "Usage: ruby delete_tweet.rb <tweet_id>"
  exit 1
end

tweet_id = ARGV[0]
delete_tweet(tweet_id) 