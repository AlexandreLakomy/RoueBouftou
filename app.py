from flask import Flask, render_template, request, jsonify
import time
import threading

app = Flask(__name__)

# Variables globales
num_players = 1
avg_tickets_per_second = 1.0  # Tickets dépensés par joueur par seconde (valeur par défaut)
timer_message = ""
timer_running = False
jackpot_timer_seconds = 0  # Minuteur pour le jackpot
time_between_jackpots = []  # Liste pour stocker les temps entre deux jackpots
last_jackpot_time = 0  # Temps de la dernière activation du jackpot
jackpot_thread = None  # Pour suivre le thread du chronomètre

# Helper function to manage the jackpot timer
def jackpot_timer():
    global jackpot_timer_seconds, timer_running
    jackpot_timer_seconds = 0
    timer_running = True
    while timer_running:
        time.sleep(1)
        jackpot_timer_seconds += 1

@app.route("/")
def roue_bouftou():
    return render_template(
        "roue_bouftou.html",
        num_players=num_players,
        timer_message=timer_message,
        time_between_jackpots=time_between_jackpots,
        avg_tickets_per_second=avg_tickets_per_second,
    )

@app.route("/update_players", methods=["POST"])
def update_players():
    global num_players
    action = request.form.get("action")
    if action == "increment":
        num_players += 1
    elif action == "decrement" and num_players > 1:
        num_players -= 1
    return jsonify({"num_players": num_players})

@app.route("/update_tickets", methods=["POST"])
def update_tickets():
    global avg_tickets_per_second
    tickets = request.form.get("tickets")
    try:
        avg_tickets_per_second = float(tickets)
        if avg_tickets_per_second < 0:
            avg_tickets_per_second = 0.0
        elif avg_tickets_per_second > 3:
            avg_tickets_per_second = 3.0
    except ValueError:
        avg_tickets_per_second = 1.0
    return jsonify({"avg_tickets_per_second": avg_tickets_per_second})

@app.route("/calculate_estimate", methods=["GET"])
def calculate_estimate():
    global avg_tickets_per_second, num_players, estimated_seconds_left
    if avg_tickets_per_second > 0:
        new_total_seconds = 1000 / avg_tickets_per_second
        # Ajuste le temps restant au lieu de réinitialiser complètement
        if "estimated_seconds_left" in globals():
            difference = new_total_seconds - estimated_seconds_left
            estimated_seconds_left += difference
        else:
            estimated_seconds_left = new_total_seconds
        mins, secs = divmod(int(estimated_seconds_left), 60)
        estimated_time = f"{mins} min {secs} sec"
    else:
        estimated_time = "N/A"
    return jsonify({"estimated_time": estimated_time, "remaining_seconds": estimated_seconds_left})


@app.route("/start_jackpot_timer", methods=["POST"])
def start_jackpot_timer():
    global timer_running, jackpot_thread, last_jackpot_time, time_between_jackpots, jackpot_timer_seconds

    if timer_running:
        # Si le minuteur tourne déjà, enregistre le temps écoulé
        mins, secs = divmod(jackpot_timer_seconds, 60)
        time_between_jackpots.insert(0, f"{len(time_between_jackpots) + 1}. {mins} min {secs} sec")
        timer_running = False  # Arrête le minuteur
        jackpot_thread.join()  # Attend que le thread se termine
        jackpot_timer_seconds = 0  # Réinitialise le temps

        # Relance un nouveau timer
        jackpot_thread = threading.Thread(target=jackpot_timer)
        jackpot_thread.start()
        timer_running = True
        return jsonify({
            "status": "success",
            "time_between_jackpots": time_between_jackpots,
        })
    else:
        # Lance le timer pour la première fois
        jackpot_thread = threading.Thread(target=jackpot_timer)
        jackpot_thread.start()
        timer_running = True
        last_jackpot_time = time.time()
        return jsonify({"status": "success"})

@app.route("/reset", methods=["POST"])
def reset():
    global time_between_jackpots, jackpot_timer_seconds, timer_running
    # Réinitialise les variables
    time_between_jackpots = []
    jackpot_timer_seconds = 0
    timer_running = False
    return jsonify({
        "status": "success",
        "timer_message": "00:00",
        "time_between_jackpots": time_between_jackpots,
    })

@app.route("/get_timer_status", methods=["GET"])
def get_timer_status():
    mins, secs = divmod(jackpot_timer_seconds, 60)
    timer_message = f"{mins:02}:{secs:02}"
    return jsonify({
        "timer_message": timer_message,
        "time_between_jackpots": time_between_jackpots,
    })

if __name__ == "__main__":
    app.run(debug=True)
