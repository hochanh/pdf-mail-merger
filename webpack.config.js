const path = require("path");
const { CleanWebpackPlugin } = require("clean-webpack-plugin");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const dotenv = require('dotenv').config();

const exclusions = /node_modules/;
const ASSET_PATH = dotenv.parsed.ASSET_PATH || '/static/';

module.exports = [
  {
    entry: {
      app: "./assets/app.js",
      editor: "./assets/editor.js",
    },
    output: {
      path: path.resolve(__dirname, "apps/static"),
      publicPath: ASSET_PATH,
      filename: "[name].js",
      chunkFilename: "[id]-[chunkhash].js",
    },
    devServer: {
      port: 8081,
      writeToDisk: true,
    },
    module: {
      rules: [
        {
          test: /.*/,
          include: path.resolve(__dirname, "assets/img"),
          exclude: exclusions,
          options: {
            context: path.resolve(__dirname, "assets/"),
            name: "[path][name].[ext]",
          },
          loader: "file-loader",
        },
        {
          test: /\.css$/,
          exclude: exclusions,
          use: [
            MiniCssExtractPlugin.loader,
            "css-loader",
            "postcss-loader",
          ],
        },
      ],
    },
    plugins: [
      new CleanWebpackPlugin({ cleanStaleWebpackAssets: false }),
      new MiniCssExtractPlugin(),
    ],
  },
];
