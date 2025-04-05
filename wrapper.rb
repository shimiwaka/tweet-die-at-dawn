#!/usr/bin/env ruby
# -*- coding: utf-8 -*-

# 引数として指定されたコマンドを実行し、その結果を返すラッパースクリプト
# 使用方法: ruby wrapper.rb "コマンド"

# コマンドが指定されていない場合はエラーを表示して終了
if ARGV.empty?
  puts "Error: No command specified"
  exit 1
end

# コマンドを取得
command = ARGV[0]

begin
  # コマンドを実行
  output = `#{command}`
  exit_status = $?.exitstatus
  
  # 結果を出力
  puts output
  
  # 終了コードを返す
  exit exit_status
rescue => e
  # エラーが発生した場合はエラーメッセージを出力
  puts "Error: #{e.message}"
  exit 1
end
