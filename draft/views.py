from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse
from django.views.generic import ListView, DetailView
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import DraftForm, ManualEnterPlayer
from .models import DraftPosition, PickedPlayers
from users.models import Profile, NflPlayers, UsersNflPlayers
from users.forms import UsersNflPlayersForm
from . import views

import pandas as pd
from math import *
import random
import numpy as np
import datetime
import math

now = datetime.datetime.now()

@login_required
def draft(request):
    if DraftPosition.objects.filter(user = request.user).exists():
        return redirect('continuedraft')
    else:
        if request.method == 'POST':
            form = DraftForm(request.POST, request.FILES)
            if form.is_valid():
                draft = form.save(commit=False)
                draft.user = request.user
                draft.save()

                #make a user model of the nfl_players model
                #create the UsersNflPlayers database for the user from the NflPlayers database
                #UsersNflPlayersForm = UsersNflPlayersForm(request.POST, request.FILES)
                nfl_players = pd.DataFrame(list(NflPlayers.objects.all().values('name','team','position','points')))
                for ind in nfl_players.index:
                    name = nfl_players['name'][ind]
                    team = nfl_players['team'][ind]
                    position = nfl_players['position'][ind]
                    points = nfl_players['points'][ind]
                    #submit the info to the model
                    player = UsersNflPlayers.objects.create(user = request.user, name = name, team = team[0], position = position[0],points = float(points))

                return redirect('running_draft')
        else:
            form = DraftForm()

        context = {
            'form' : form,
        }
        return render(request, 'draft/draft.html', context)

@login_required
def continuedraft(request):
    if request.method == 'POST':
        if request.POST.get("continue"):
            return redirect('running_draft')
        elif request.POST.get("start_over"):
            #if starting over delete the draft position and picked players from database
            DraftPosition.objects.filter(user = request.user).delete()
            PickedPlayers.objects.filter(user = request.user).delete()
            UsersNflPlayers.objects.filter(user = request.user).delete()
            return redirect('draft')
    else:
        players_draft_position = DraftPosition.objects.values_list('draftposition',flat=True).filter(user = request.user)
        players_draft_position = players_draft_position[0]
        num_rounds_list = Profile.objects.values_list('numberofplayersperteam',flat=True).filter(user = request.user)
        num_rounds = num_rounds_list[0]
        countofplayers = len(PickedPlayers.objects.all().filter(user = request.user, rosterteam = 1, season=now.year))
        myteam = PickedPlayers.objects.all().filter(user = request.user, rosterteam = players_draft_position, season=now.year)

        if countofplayers < num_rounds:
            status = "active"
        else:
            status = "complete"
        return render(request, 'draft/continuedraft.html', {'players_draft_position' : players_draft_position, 'title':'Continue','status':status,'myteam':myteam})


@login_required
def running_draft(request):
    #need to remember to delete users DRAFT object once the draft has finished
    players_draft_position = DraftPosition.objects.values_list('draftposition',flat=True).filter(user = request.user)
    #get the list of nfl players from the database
    nfl_players = pd.DataFrame(list(NflPlayers.objects.all().values('name','team','position','points')))
    #get then number of players in the league
    num_competitors_list = Profile.objects.values_list('numberofteamsinleague',flat=True).filter(user = request.user)  #numberofteamsinleague
    num_competitors = num_competitors_list[0]

    #rosters is technically the picked players that the algorithm uses to decided the next best player
    rosters = [[] for _ in range(num_competitors)]
    #fill the empty rosters with the already picked players
    if PickedPlayers.objects.filter(user = request.user).exists():
        mypickedplayers = PickedPlayers.objects.values('rosterteam','name','team','position','points').filter(user = request.user, season=now.year)
        for p in mypickedplayers:
            rosterteam = p.get('rosterteam')-1
            name = p.get('name')
            team = p.get('team')
            position = p.get('position')
            points = p.get('points')
            rosters[rosterteam].append(NflPlayer(name, team, position, points))

    #remove the users PickedPlayers from the default dataframe
    if PickedPlayers.objects.filter(user = request.user).exists():
        mypickedplayers = PickedPlayers.objects.values('rosterteam','name','team','position').filter(user = request.user, season=now.year)
        for p in mypickedplayers:
            name = p.get('name')
            team = p.get('team')
            position = p.get('position')
            indexNames = nfl_players[ (nfl_players['name'] == name) & (nfl_players['team'] == team) & (nfl_players['position'] == position)].index
            nfl_players.drop(indexNames , inplace=True)
    freeagents = [NflPlayer(*p) for p in nfl_players.itertuples(index=False, name=None)]
    #use the number of players in the league to create the dict and remove the players pick position to create the manual picking places
    manual_pic_positions = list(range(0,int(num_competitors)))
    automatic_pic_remove = manual_pic_positions.pop(players_draft_position[0]-1)

    num_rounds_list = Profile.objects.values_list('numberofplayersperteam',flat=True).filter(user = request.user)
    num_rounds = num_rounds_list[0]

    turnstaken = len(PickedPlayers.objects.values('rosterteam','name','team','position').filter(user = request.user, season=now.year))
    turns = []
    # generate turns by snake order
    for i in range(num_rounds):
        turns += reversed(range(num_competitors)) if i % 2 else range(num_competitors)
    turns = turns[turnstaken:]
    state = DraftState(rosters, turns, freeagents, request.user)

    if state.ManualGetMoves() != []:
        if state.turns[0] in manual_pic_positions:
            #put up a form that says enter manual teams pick
            #How to Implement Dependent/Chained Dropdown List with Django
            #https://simpleisbetterthancomplex.com/tutorial/2018/01/29/how-to-implement-dependent-or-chained-dropdown-list-with-django.html
            pick = 'manual'
            rosterteam = turns[0]+1
            if request.method == 'POST':
                form = ManualEnterPlayer(request.user, request.POST, request.FILES)
                if form.is_valid():
                    name = form.cleaned_data.get('name')
                    team = NflPlayers.objects.values_list('team',flat=True).filter(name = name)
                    if turnstaken == 0:
                        draftround = 1
                    else:
                        draftround = math.ceil((turnstaken+.5)/num_competitors)
                    rosterteam = rosterteam
                    position = NflPlayers.objects.values_list('position',flat=True).filter(name = name)
                    points = NflPlayers.objects.values_list('points',flat=True).filter(name = name)
                    #submit the info to the model
                    pickedplayer = PickedPlayers.objects.create(user = request.user, name = name, team = team[0], draftround = draftround, rosterteam = rosterteam,position = position[0],points = points[0])
                    #delete from users list
                    UsersNflPlayers.objects.filter(user = request.user, name = name).delete()
                    return redirect ('running_draft')
            else:
                form = ManualEnterPlayer(request.user)
                if turnstaken == 0:
                    draftround = 1
                else:
                    draftround = math.ceil((turnstaken+.5)/num_competitors)

            players_draft_position = DraftPosition.objects.values_list('draftposition',flat=True).filter(user = request.user)
            players_draft_position = players_draft_position[0]
            myteam = PickedPlayers.objects.all().filter(user = request.user, rosterteam = players_draft_position, season=now.year)

            context = {
                'form' : form,
                'pick' : pick,
                'rosterteam' : rosterteam,
                'draftround' : draftround,
                'myteam':myteam,
            }
        else:
            if turnstaken == 0:
                draftround = 1
            else:
                draftround = math.ceil((turnstaken+.5)/num_competitors)

            players_draft_position = DraftPosition.objects.values_list('draftposition',flat=True).filter(user = request.user)
            players_draft_position = players_draft_position[0]
            myteam = PickedPlayers.objects.all().filter(user = request.user, rosterteam = players_draft_position, season=now.year)

            context = {
                'draftround' : draftround,
                'myteam':myteam,
            }

        return render(request, 'draft/running_draft.html', context)
    else:
        return redirect ('complete')




@login_required
def mypick(request):
    #kick off the celery task
    players_draft_position = DraftPosition.objects.values_list('draftposition',flat=True).filter(user = request.user)
    #get the list of nfl players from the database
    nfl_players = pd.DataFrame(list(NflPlayers.objects.all().values('name','team','position','points')))
    #get then number of players in the league
    num_competitors_list = Profile.objects.values_list('numberofteamsinleague',flat=True).filter(user = request.user)  #numberofteamsinleague
    num_competitors = num_competitors_list[0]
    #rosters is technically the picked players that the algorithm uses to decided the next best player
    rosters = [[] for _ in range(num_competitors)]
    #fill the empty rosters with the already picked players
    if PickedPlayers.objects.filter(user = request.user).exists():
        mypickedplayers = PickedPlayers.objects.values('rosterteam','name','team','position','points').filter(user = request.user, season=now.year)
        for p in mypickedplayers:
            rosterteam = p.get('rosterteam')-1
            name = p.get('name')
            team = p.get('team')
            position = p.get('position')
            points = p.get('points')
            rosters[rosterteam].append(NflPlayer(name, team, position, points))

    #remove the users PickedPlayers from the default dataframe
    if PickedPlayers.objects.filter(user = request.user).exists():
        mypickedplayers = PickedPlayers.objects.values('rosterteam','name','team','position').filter(user = request.user, season=now.year)
        for p in mypickedplayers:
            name = p.get('name')
            team = p.get('team')
            position = p.get('position')
            indexNames = nfl_players[ (nfl_players['name'] == name) & (nfl_players['team'] == team) & (nfl_players['position'] == position)].index
            nfl_players.drop(indexNames , inplace=True)
    freeagents = [NflPlayer(*p) for p in nfl_players.itertuples(index=False, name=None)]
    num_rounds_list = Profile.objects.values_list('numberofplayersperteam',flat=True).filter(user = request.user)
    num_rounds = num_rounds_list[0]

    turnstaken = len(PickedPlayers.objects.values('rosterteam','name','team','position').filter(user = request.user, season=now.year))
    turns = []
    # generate turns by snake order
    for i in range(num_rounds):
        turns += reversed(range(num_competitors)) if i % 2 else range(num_competitors)
    turns = turns[turnstaken:]
    #get users max positions from model to pass
    qb = Profile.objects.values_list('qb',flat=True).filter(user = request.user)
    rb = Profile.objects.values_list('rb',flat=True).filter(user = request.user)
    wr = Profile.objects.values_list('wr',flat=True).filter(user = request.user)
    te = Profile.objects.values_list('te',flat=True).filter(user = request.user)
    d = Profile.objects.values_list('d',flat=True).filter(user = request.user)
    k = Profile.objects.values_list('k',flat=True).filter(user = request.user)
    pos_max = {"QB": qb[0], "WR": wr[0], "RB": rb[0], "TE": te[0], "D": d[0], "K": k[0]}

    state = DraftState(rosters, turns, freeagents, pos_max)
    iterations = 1000 #1000 is ample for the moves
    move = UCT(state, iterations, pos_max)
    player = state.ShowPick(move)
    rosterteam = turns[0]+1 #the team number of the draftee

    if request.method == 'POST':
        choiceselection = request.POST.get("choice")
        if choiceselection == "accept":
            name = player
            team = NflPlayers.objects.values_list('team',flat=True).filter(name = name)
            if turnstaken == 0:
                draftround = 1
            else:
                draftround = math.ceil((turnstaken+.5)/num_competitors)
            rosterteam = rosterteam
            position = NflPlayers.objects.values_list('position',flat=True).filter(name = name)
            points = NflPlayers.objects.values_list('points',flat=True).filter(name = name)
            #submit the info to the model
            pickedplayer = PickedPlayers.objects.create(user = request.user, name = name, team = team[0], draftround = draftround, rosterteam = rosterteam, position = position[0],points = points[0])
            #delete player from UsersNflPlayers database
            UsersNflPlayers.objects.filter(user = request.user, name = name).delete()
            return redirect('running_draft')

        elif request.POST.get("choose"):
            form = ManualEnterPlayer(request.user, request.POST, request.FILES)
            if form.is_valid():
                name = form.cleaned_data.get('name')
                team = NflPlayers.objects.values_list('team',flat=True).filter(name = name)
                if turnstaken == 0:
                    draftround = 1
                else:
                    draftround = math.ceil((turnstaken+.5)/num_competitors)
                rosterteam = rosterteam
                position = NflPlayers.objects.values_list('position',flat=True).filter(name = name)
                points = NflPlayers.objects.values_list('points',flat=True).filter(name = name)
                #submit the info to the model
                pickedplayer = PickedPlayers.objects.create(user = request.user, name = name, team = team[0], draftround = draftround, rosterteam = rosterteam, position = position[0], points = points[0])
                #delete player from UsersNflPlayers database
                UsersNflPlayers.objects.filter(user = request.user, name = name).delete()

                return redirect('running_draft')

        else:
            players_draft_position = DraftPosition.objects.values_list('draftposition',flat=True).filter(user = request.user)
            players_draft_position = players_draft_position[0]
            myteam = PickedPlayers.objects.all().filter(user = request.user, rosterteam = players_draft_position, season=now.year)

            form = ManualEnterPlayer(request.user)
            return render(request, 'draft/mypick.html', {'title':'My Team', 'move':move, 'player':player, 'form':form, 'myteam':myteam})



def complete(request):
    players_draft_position = DraftPosition.objects.values_list('draftposition',flat=True).filter(user = request.user)
    players_draft_position = players_draft_position[0]
    results = PickedPlayers.objects.all().filter(user = request.user, rosterteam = players_draft_position, season=now.year)
    UsersNflPlayers.objects.filter(user = request.user).delete()

    return render(request, 'draft/complete.html', { 'results': results })




#below are all of the draft functions

class DraftState:
    def __init__(self, rosters, turns, freeagents, pos_max, playerjm=None):
        self.rosters = rosters
        self.turns = turns
        self.freeagents = freeagents
        self.playerJustMoved = playerjm
        self.pos_max = pos_max

class NflPlayer:
    def __init__(self, name, team, position, points):
        self.name = name
        self.team = team
        self.position = position
        self.points = points

    def __repr__(self):
        return "|".join([self.name, self.team, self.position, str(self.points)])

def GetResult(self, playerjm):
    """ Get the game result from the viewpoint of playerjm.
    """
    if playerjm is None: return 0

    pos_wgts = {
        ("QB"): [.6, .4],
        ("WR"): [.7, .7, .3, .3],
        ("RB"): [.7, .7, .4, .2],
        ("TE"): [.6, .4],
        ("RB", "WR", "TE"): [.6, .4],
        ("D"): [.6, .3, .1],
        ("K"): [.4, .3, .2, .1]
    }

    result = 0
    # map the drafted players to the weights
    for p in self.rosters[playerjm]:
        max_wgt, _, max_pos, old_wgts = max(
            ((wgts[0], -len(lineup_pos), lineup_pos, wgts) for lineup_pos, wgts in pos_wgts.items()
                if p.position in lineup_pos),
            default=(0, 0, (), []))
        if max_wgt > 0:
            result += max_wgt * int(p.points)
            old_wgts.pop(0)
            if not old_wgts:
                pos_wgts.pop(max_pos)

    # map the remaining weights to the top three free agents
    for pos, wgts in pos_wgts.items():
        result += np.mean([int(p.points) for p in self.freeagents if p.position in pos][:3]) * sum(wgts)

    return result

DraftState.GetResult = GetResult

def ManualGetMoves(self):
    """ Get all possible moves from this state.
    """
    pos_max = {"QB": 2, "WR": 6, "RB": 6, "TE": 2, "D": 2, "K": 2}

    if len(self.turns) == 0:
        return []

    roster_positions = np.array([p.position for p in self.rosters[self.turns[0]]], dtype=str)
    moves = [pos for pos, max_ in pos_max.items() if np.sum(roster_positions == pos) < max_]
    return moves

DraftState.ManualGetMoves = ManualGetMoves


def GetMoves(self,pos_max):
    """ Get all possible moves from this state.
    """
    if len(self.turns) == 0:
        return []

    roster_positions = np.array([p.position for p in self.rosters[self.turns[0]]], dtype=str)
    moves = [pos for pos, max_ in pos_max.items() if np.sum(roster_positions == pos) < max_]
    pos_max = self.pos_max
    return moves

DraftState.GetMoves = GetMoves


def DoMove(self, move):
    """ Update a state by carrying out the given move.
        Must update playerJustMoved.
    """
    player = next(p for p in self.freeagents if p.position == move)
    self.freeagents.remove(player)
    rosterId = self.turns.pop(0)
    self.rosters[rosterId].append(player)
    self.playerJustMoved = rosterId

DraftState.DoMove = DoMove


def ShowPick(self, move):
    """ Show what the suggested next pic would be.
    """
    player = next(p for p in self.freeagents if p.position == move)
    return player.name

DraftState.ShowPick = ShowPick


def Clone(self):
    """ Create a deep clone of this game state.
    """
    pos_max = self.pos_max
    rosters = list(map(lambda r: r[:], self.rosters))
    st = DraftState(rosters, self.turns[:], self.freeagents[:],
            self.playerJustMoved, pos_max)

    return st

DraftState.Clone = Clone

# This is a very simple implementation of the UCT Monte Carlo Tree Search algorithm in Python 2.7.
# The function UCT(rootstate, itermax, verbose = False) is towards the bottom of the code.
# It aims to have the clearest and simplest possible code, and for the sake of clarity, the code
# is orders of magnitude less efficient than it could be made, particularly by using a
# state.GetRandomMove() or state.DoRandomRollout() function.
#
# Written by Peter Cowling, Ed Powley, Daniel Whitehouse (University of York, UK) September 2012.
#
# Licence is granted to freely use and distribute for any sensible/legal purpose so long as this comment
# remains in any distributed code.
#
# For more information about Monte Carlo Tree Search check out our web site at www.mcts.ai

class Node:
    """ A node in the game tree. Note wins is always from the viewpoint of playerJustMoved.
        Crashes if state not specified.
    """
    def __init__(self, pos_max, move = None, parent = None, state = None):
        self.move = move # the move that got us to this node - "None" for the root node
        self.parentNode = parent # "None" for the root node
        self.childNodes = []
        self.wins = 0
        self.visits = 0
        self.pos_max = pos_max
        self.untriedMoves = state.GetMoves(pos_max) # future child nodes
        self.playerJustMoved = state.playerJustMoved # the only part of the state that the Node needs later

    def UCTSelectChild(self):
        """ Use the UCB1 formula to select a child node. Often a constant UCTK is applied so we have
            lambda c: c.wins/c.visits + UCTK * sqrt(2*log(self.visits)/c.visits to vary the amount of
            exploration versus exploitation.
        """
        UCTK = 200
        s = sorted(self.childNodes, key = lambda c: c.wins/c.visits + UCTK * sqrt(2*log(self.visits)/c.visits))[-1]
        return s

    def AddChild(self, pos_max, m, s):
        """ Remove m from untriedMoves and add a new child node for this move.
            Return the added child node
        """
        n = Node(pos_max, move = m, parent = self, state = s)
        self.untriedMoves.remove(m)
        self.childNodes.append(n)
        return n

    def Update(self, result):
        """ Update this node - one additional visit and result additional wins. result must be from the viewpoint of playerJustmoved.
        """
        self.visits += 1
        self.wins += result



def UCT(rootstate, itermax, pos_max, verbose = False):
    """ Conduct a UCT search for itermax iterations starting from rootstate.
        Return the best move from the rootstate.
    """

    rootnode = Node(pos_max, state = rootstate)

    for i in range(itermax):
        node = rootnode
        state = rootstate.Clone()

        # Select
        while node.untriedMoves == [] and node.childNodes != []: # node is fully expanded and non-terminal
            node = node.UCTSelectChild()
            state.DoMove(node.move)

        # Expand
        if node.untriedMoves != []: # if we can expand (i.e. state/node is non-terminal)
            m = random.choice(node.untriedMoves)
            state.DoMove(m)
            node = node.AddChild(pos_max, m, state) # add child and descend tree

        # Rollout - this can often be made orders of magnitude quicker using a state.GetRandomMove() function
        while state.GetMoves(pos_max) != []: # while state is non-terminal
            state.DoMove(random.choice(state.GetMoves(pos_max)))


        # Backpropagate
        while node != None: # backpropagate from the expanded node and work back to the root node
            node.Update(state.GetResult(node.playerJustMoved)) # state is terminal. Update node with result from POV of node.playerJustMoved
            node = node.parentNode

    return sorted(rootnode.childNodes, key = lambda c: c.visits)[-1].move # return the move that was most visited
