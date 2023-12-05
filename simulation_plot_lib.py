from collections import Counter
import json
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

metrics = None
data = None

def calculate_metrics(overwrite=False):
    global metrics
    global data
    

    if metrics != None and not overwrite:
        return metrics

    # Load JSON data from the file
    with open('batch_game_log.json') as json_file:
        data = json.load(json_file)
    # Convert yellow to orange for better visibility
    if "yellow" in data["players"].keys(): 
        data["players"]["orange"] = data["players"].pop("yellow")

    metrics = {}
    # Extract relevant data
    metrics["colors"] = list(data['players'].keys())
    metrics["n"] = data['games_played']

    # Calculate metrics
    for color in metrics["colors"]:
        color_metrics = {}
        player_data = data['players'][color]

        color_metrics["strategy"] = player_data["strategy"]
        
        color_metrics["win_rates"] =  np.mean(player_data['games_won']) / 100
        
        color_metrics["average_tokens_captured"] = np.mean(player_data['tokens_captured'])
        color_metrics["average_tokens_lost"] = np.mean(player_data['tokens_beaten'])
        color_metrics["average_squares_moved"] = np.mean(player_data['total_squares_moved'])
        
        turns_until_win = [x for x in player_data['turns_until_win'] if x is not False]
        color_metrics["average_turns_until_win"] = np.mean(turns_until_win) if turns_until_win else 0


        cumulative_wins = [sum(player_data['games_won'][:i+1]) for i in range(len(player_data['games_won']))]
        color_metrics["win_rates_over_time"] =  [x / (i+1) for i, x in enumerate(cumulative_wins)]

        won_tokens_captured = np.zeros(max(player_data["tokens_captured"])+1)
        lost_tokens_beaten = np.zeros(max(player_data["tokens_beaten"])+1)
        lost_tokens_captured = np.zeros(max(player_data["tokens_captured"])+1)
        won_tokens_beaten = np.zeros(max(player_data["tokens_beaten"])+1)
        lost_tokens_beaten = np.zeros(max(player_data["tokens_beaten"])+1)
        lost_turns_taken = np.zeros(max(player_data["turns_taken"])+1)
        won_turns_taken = np.zeros(max(player_data["turns_taken"])+1)


        for turns_taken, captured_tokens, tokens_beaten, won in zip(player_data["turns_taken"], player_data["tokens_captured"], player_data["tokens_beaten"], player_data["games_won"]):
            if won:
                won_tokens_captured[captured_tokens] += 1
                won_tokens_beaten[tokens_beaten] += 1
                won_turns_taken[turns_taken] += 1
            else:
                lost_tokens_beaten[tokens_beaten] += 1
                lost_tokens_captured[captured_tokens] += 1
                lost_turns_taken[turns_taken] += 1

        color_metrics["games_won_by_tokens_captured"] = won_tokens_captured
        color_metrics["games_lost_by_tokens_beaten"] = lost_tokens_beaten
        color_metrics["games_lost_by_tokens_captured"] = lost_tokens_captured
        color_metrics["games_won_by_tokens_beaten"] = won_tokens_beaten
        color_metrics["games_lost_by_tokens_beaten"] = lost_tokens_beaten
        color_metrics["games_lost_by_turns_taken"] = lost_turns_taken
        color_metrics["games_won_by_turns_taken"] = won_turns_taken

        metrics[color] = color_metrics

    return metrics

def player_metric_pie(metric_name: str, title: str, red = True, green = True, blue = True, orange = True):
    calculate_metrics()

    enabled = {"red": red, "green": green, "blue": blue, "orange": orange}

    plt.figure(figsize=(5, 3))

    y_datas = []
    for color in metrics["colors"]:
        if enabled[color]:
            color_metrics = metrics[color]
            if isinstance(color_metrics[metric_name], list):
                y_data = [value for value in color_metrics[metric_name] if not isinstance(value, bool)]
            else:
                y_data = color_metrics[metric_name]
            y_datas.append(y_data)
    
    plt.pie(y_datas, colors=metrics["colors"], labels=[metrics[color]["strategy"] for color in metrics["colors"]], autopct='%1.0f%%')
    

    plt.show()

def player_metric_line(metric_name: str, x_label: str,  y_label: str, title: str, red = True, green = True, blue = True, orange = True):
    calculate_metrics()

    enabled = {"red": red, "green": green, "blue": blue, "orange": orange}

    plt.figure(figsize=(5, 3))

    for color in metrics["colors"]:
        if enabled[color]:
            color_metrics = metrics[color]
            y_data = [value for value in color_metrics[metric_name] if not isinstance(value, bool)]
            plt.plot(y_data, color=color, label=color_metrics["strategy"])
    
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    

    plt.legend()
    plt.show()

def player_metric_lines(metric_names: list[str], x_label: str,  y_label: str, title: str, colors: list[str] = [], labels: list[str] = [], red = True, green = True, blue = True, orange = True):
    calculate_metrics()

    enabled = {"red": red, "green": green, "blue": blue, "orange": orange}
    
    fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(6, 4))
    axes = axes.flatten()

    for color_index, color in enumerate(metrics["colors"]):
        if enabled[color]:
            ax = axes[color_index]
            color_metrics = metrics[color]
            for metrics_index, metric in enumerate(metric_names):
                special_color = colors[metrics_index] if metrics_index < len(colors) else color
                special_label = labels[metrics_index] if metrics_index < len(labels) else None
                y_data = [value for value in color_metrics[metric] if not isinstance(value, bool)]
                ax.plot(y_data, label=special_label, color=special_color)
                ax.set_xlabel(x_label)
                ax.set_ylabel(y_label)
                ax.set_title(color_metrics["strategy"])
                ax.legend()

    
    plt.show()

def player_metric_bar(metric_name: str, y_label: str, title: str, red = True, green = True, blue = True, orange = True):
    calculate_metrics()

    enabled = {"red": red, "green": green, "blue": blue, "orange": orange}

    plt.figure(figsize=(5, 3))

    for color in metrics["colors"]:
        if enabled[color]:
            color_metrics = metrics[color]
            if isinstance(color_metrics[metric_name], list):
                y_data = [value for value in color_metrics[metric_name] if not isinstance(value, bool)]
            else:
                y_data = color_metrics[metric_name]
            plt.bar(color_metrics["strategy"], y_data, color=color)
    
    plt.xlabel('Strategies')
    plt.ylabel(y_label)
    

    plt.show()

def player_metric_bars(metric_names: list[str], y_label: str, title: str, colors: list[str] = [], labels: list[str] = [], red = True, green = True, blue = True, orange = True):
    calculate_metrics()
    enabled = {"red": red, "green": green, "blue": blue, "orange": orange}
    bar_width = 0.35

    plt.figure(figsize=(5, 3))

    for color_index, color in enumerate(metrics["colors"]):
        if enabled[color]:
            color_metrics = metrics[color]
            for metrics_index, metric in enumerate(metric_names):
                special_color = colors[metrics_index] if metrics_index < len(colors) else None
                if isinstance(color_metrics[metric], list):
                    y_data = [value for value in color_metrics[metric] if not isinstance(value, bool)]
                else:
                    y_data = color_metrics[metric]
                plt.bar(color_index + bar_width * metrics_index, y_data, color=special_color, edgecolor=color, width=bar_width, label=labels[metrics_index])
    
    
    plt.xticks([r + bar_width/2 for r in range(len(metrics["colors"]))], [metrics[color]["strategy"] for color in metrics["colors"]])
    plt.xlabel('Strategies')
    plt.ylabel(y_label)
    
    
    # Avoid duplicate legend labels
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    plt.legend(by_label.values(), by_label.keys())

    plt.show()

def player_data_histogram(data_name: str, x_label: str, y_label: str, title: str, bin_num: int, normalize: bool = False, overlapping: bool = False, red = True, green = True, blue = True, orange = True):
    calculate_metrics()
    enabled = {"red": red, "green": green, "blue": blue, "orange": orange}
    
    plt.figure(figsize=(5, 3))

    included = [color for color in metrics["colors"] if enabled[color]]

    max_value = max([value for sublist in [data['players'][color][data_name] for color in included] for value in sublist])
    bins = np.linspace(0, max_value, bin_num)

    if overlapping:
        for color in metrics["colors"]:
            if enabled[color]:
                color_metrics = metrics[color]
                y_data = [value for value in data['players'][color][data_name] if not isinstance(value, bool)]
                plt.hist(y_data, bins, alpha=0.4, label=color_metrics["strategy"], color=color, edgecolor="black", density=normalize)
    else:
        y_datas = []
        for color in metrics["colors"]:
            if enabled[color]:
                color_metrics = metrics[color]
                y_data = [value for value in data['players'][color][data_name] if not isinstance(value, bool)]
                y_datas.append(y_data)
        plt.hist(y_datas, bins, label=[metrics[color]["strategy"] for color in included], color=[color for color in included], density=normalize)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    
    plt.legend()
    plt.show()
    plt.show()

def player_data_gauss_fit(data_name: str, x_label: str, y_label: str, title: str, resolution: int, normalize: bool = False, red = True, green = True, blue = True, orange = True):
    calculate_metrics()
    enabled = {"red": red, "green": green, "blue": blue, "orange": orange}
    
    plt.figure(figsize=(5, 3))

    for color in metrics["colors"]:
        if enabled[color]:
            y_data = [value for value in data['players'][color][data_name] if not isinstance(value, bool)]
            mean,std = norm.fit(y_data)
            x = np.linspace(min(y_data), max(y_data), resolution)
            plt.plot(x, norm.pdf(x, mean, std), label=metrics[color]["strategy"], color=color)

    plt.xlabel(x_label)
    plt.ylabel(y_label)
    
    plt.legend()
    plt.show()


def player_data_scatter(data_name1: str, data_name2: str, x_label: str, y_label: str, title: str):
    calculate_metrics()

    fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(10, 8))
    axes = axes.flatten()

    for index, color in enumerate(metrics["colors"]):
        x = [value for value in data['players'][color][data_name1] if not isinstance(value, bool)]
        y = [value for value in data['players'][color][data_name2] if not isinstance(value, bool)]
        c = Counter(zip(x,y))
        s = [c[(xx,yy)] for xx,yy in zip(x,y)]
        ax = axes[index]
        ax.scatter(x, y, color=color, s=s, marker=".")
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_title(metrics[color]["strategy"])

    plt.show()


# Exmaple usages

player_metric_line(metric_name="games_won_by_tokens_captured", 
                x_label="Tokens Captured", 
                y_label="Games Won", 
                title="Games Won by Token Captured")

player_metric_line(metric_name="games_lost_by_tokens_beaten", 
                x_label="Tokens Beaten", 
                y_label="Games Lost", 
                title="Games Lost by Token Beaten")

player_metric_line(metric_name="games_won_by_turns_taken", 
                x_label="Turns Taken", 
                y_label="Games Won", 
                title="Games Won by Turns Taken")

player_metric_lines(metric_names=["games_won_by_turns_taken", "games_lost_by_turns_taken"], 
                x_label="Turns Taken", 
                y_label="Games Won/Lost", 
                colors=["lightgreen", "lightcoral"],
                labels=["Games Won", "Games Lost"],
                title="Games Won/Lost by Turns Taken")


player_metric_bar(metric_name="win_rates", 
                y_label="Percentage of Games Won", 
                title="Strategy Winrates")

player_metric_pie(metric_name="win_rates", 
                title="Strategy Winrates")

player_metric_bars(metric_names=["average_tokens_captured", "average_tokens_lost"], 
                 y_label="Tokens", 
                 title="Tokens Captured/Lost by Strategy", 
                 colors=["lightgreen", "lightcoral"],
                 labels=["Tokens Captured", "Tokens Lost"])

player_data_histogram(data_name="total_squares_moved",
                      x_label="Squares Moved per Game",
                      y_label="Frequency",
                      title="Histogram of Moved Squares by Strategy",
                      bin_num=30)

player_data_gauss_fit(data_name="total_squares_moved",
                      x_label="Squares Moved per Game",
                      y_label="Frequency",
                      title="Distribution of Moved Squares by Strategy",
                      resolution=100)

player_data_scatter(data_name1="total_squares_moved", 
                    data_name2="tokens_captured",
                    x_label="Total Squares Moved",
                    y_label="Tokens Captured",
                    title="Scatter Plots of X")

player_data_histogram(data_name="turns_until_win",
                      x_label="Turns Until Win",
                      y_label="Frequency",
                      title="Histogram of Turns Until Win by Strategy",
                      bin_num=30)

player_data_gauss_fit(data_name="turns_until_win",
                      x_label="Turns Until Win",
                      y_label="Frequency",
                      title="Distribution of Turns Until Win by Strategy",
                      resolution=100)

player_metric_line(metric_name="win_rates_over_time", 
                x_label="Games Played", 
                y_label="Win Rate", 
                title="Win Rates Over Time")